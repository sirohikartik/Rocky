const fs = require('fs');
const ph = require('path');
const { execSync: ex } = require('child_process');

const FP = 30; // Framerate for parsing video
const DT = +(1 / FP).toFixed(4); // Duration per discrete frame
const VI = process.argv[2] || ph.resolve(__dirname, 'models', 'MVI_2989.mov');
const OT = process.argv[3] || ph.resolve(__dirname, 'models', 'vrm_animation.json');
const CD = ph.resolve(__dirname, 'models', '_cache');
const PU = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task';
const HU = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task';
const PM = ph.join(CD, 'pose_landmarker_full.task');
const HM = ph.join(CD, 'hand_landmarker.task');
const TF = ph.join(CD, '_lm.json');

fs.mkdirSync(CD, { recursive: true });

function dl(u, f) {
  if (fs.existsSync(f)) return;
  console.log('DL ' + ph.basename(f));
  const sc = ph.join(CD, '_dl.cjs');
  fs.writeFileSync(sc, [
    `const h=require('https'),fs=require('fs');`,
    `function g(u,p){h.get(u,r=>{`,
    `if(r.statusCode>=300&&r.statusCode<400)return g(r.headers.location,p);`,
    `const s=fs.createWriteStream(p);r.pipe(s);`,
    `s.on('finish',()=>{s.close();process.exit(0)})`,
    `}).on('error',e=>{console.error(e.message);process.exit(1)})};`,
    `g(process.argv[2],process.argv[3]);`
  ].join(''));
  ex(`node "${sc}" "${u}" "${f}"`, { stdio: 'inherit', timeout: 300000 });
}

dl(PU, PM);
dl(HU, HM);

const PY = `import mediapipe as mp,cv2,json,sys
BO=mp.tasks.BaseOptions
PL=mp.tasks.vision.PoseLandmarker
PLO=mp.tasks.vision.PoseLandmarkerOptions
HL=mp.tasks.vision.HandLandmarker
HLO=mp.tasks.vision.HandLandmarkerOptions
RM=mp.tasks.vision.RunningMode
po=PLO(base_options=BO(model_asset_path=sys.argv[3]),running_mode=RM.VIDEO)
ho=HLO(base_options=BO(model_asset_path=sys.argv[4]),running_mode=RM.VIDEO,num_hands=2)
pl=PL.create_from_options(po)
hl=HL.create_from_options(ho)
cap=cv2.VideoCapture(sys.argv[1])
fps=cap.get(cv2.CAP_PROP_FPS)
tar=int(sys.argv[2])
sk=max(1,int(fps/tar))
fr=[]
ix=0
while cap.isOpened():
    ret,img=cap.read()
    if not ret:break
    if ix%sk!=0:
        ix+=1
        continue
    rgb=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    mi=mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb)
    ts=int(ix*1000/fps)
    pr=pl.detect_for_video(mi,ts)
    hr=hl.detect_for_video(mi,ts)
    fd={"ts":ts,"w":img.shape[1],"h":img.shape[0]}
    if pr.pose_landmarks:
        fd["p2"]=[{"x":l.x,"y":l.y,"z":l.z,"visibility":l.visibility}for l in pr.pose_landmarks[0]]
    if pr.pose_world_landmarks:
        fd["p3"]=[{"x":l.x,"y":l.y,"z":l.z,"visibility":l.visibility}for l in pr.pose_world_landmarks[0]]
    if hr.hand_landmarks:
        for i,h in enumerate(hr.hand_landmarks):
            sd=hr.handedness[i][0].category_name
            k="lh" if sd=="Left" else "rh"
            fd[k]=[{"x":l.x,"y":l.y,"z":l.z}for l in h]
    fr.append(fd)
    if len(fr)%10==0:
        print(f"  {len(fr)} frames...",flush=True)
    ix+=1
cap.release()
print(f"  {len(fr)} frames total")
with open(sys.argv[5],'w')as f:
    json.dump(fr,f)
`;

const pf = ph.join(CD, '_ex.py');
fs.writeFileSync(pf, PY);

console.log('=== Step 1: Extracting landmarks ===');
console.log('  Video: ' + ph.basename(VI));
console.log('  Target FPS: ' + FP);
ex(`python "${pf}" "${VI}" ${FP} "${PM}" "${HM}" "${TF}"`, {
  stdio: 'inherit',
  timeout: 600000
});

if (!fs.existsSync(TF)) { console.error('Landmark extraction failed'); process.exit(1); }

const lm = JSON.parse(fs.readFileSync(TF, 'utf-8'));
console.log('\n=== Step 2: Running Kalidokit solver ===');
console.log('  ' + lm.length + ' frames to process');

let K = require(ph.resolve(__dirname, 'client', 'node_modules', 'kalidokit', 'dist', 'kalidokit.umd.js'));
if (K.default) K = K.default;
const PS = K.Pose;
const HS = K.Hand;
if (!PS || !HS) { console.error('Kalidokit unavailable'); process.exit(1); }



const cl = (v, lo, hi) => Math.max(lo, Math.min(hi, v || 0));
const PI = Math.PI;
const H  = PI / 2;  // 90°

function mpa(rp) {
  if (!rp) return {};
  let bn = {};

  // Upper arm: allow full ±180° so the idle z=1.22 rad (70°) resting pose is never clipped.
  let ua = (k) => {
    let v = rp[k];
    if (!v) return;
    let nm = k[0].toLowerCase() + k.slice(1);
    bn[nm] = { x: 0, y: cl(v.y, -H, H), z: cl(v.z, -PI, PI) };
  };

  // Lower arm: elbow hinge on y, symmetric clamp — sign differs between left and right arms.
  let la = (k) => {
    let v = rp[k];
    if (!v) return;
    let nm = k[0].toLowerCase() + k.slice(1);
    bn[nm] = { x: 0, y: cl(v.y, -2.6, 2.6), z: 0 };
  };

  // Spine / chest / neck: small rotations only to avoid exaggerated torso lean.
  let cp = (k) => {
    let v = rp[k];
    if (!v) return;
    let nm = k.toLowerCase();
    bn[nm] = { x: cl(v.x, -0.4, 0.4), y: cl(v.y, -0.3, 0.3), z: cl(v.z, -0.3, 0.3) };
  };

  ua('RightUpperArm');
  ua('LeftUpperArm');
  la('RightLowerArm');
  la('LeftLowerArm');

  if (rp.RightHand) bn.rightHand = { x: cl(rp.RightHand.x, -H, H), y: cl(rp.RightHand.y, -H, H), z: cl(rp.RightHand.z, -H, H) };
  if (rp.LeftHand)  bn.leftHand  = { x: cl(rp.LeftHand.x,  -H, H), y: cl(rp.LeftHand.y,  -H, H), z: cl(rp.LeftHand.z,  -H, H) };

  cp('Spine');
  cp('Chest');
  cp('Neck');

  return bn;
}

function mhd(rh, sd) {
  if (!rh) return {};
  let bn = {};
  let pr = sd === 'Right' ? 'right' : 'left';
  for (let d of ['Thumb', 'Index', 'Middle', 'Ring', 'Little']) {
    for (let s of ['Proximal', 'Intermediate', 'Distal']) {
      let v = rh[sd + d + s];
      if (!v) continue;
      // VRM finger curl is on z; clamp to 0–90° open-to-closed. Suppress spurious x/y spread.
      bn[pr + d + s] = { x: cl(v.x, -0.3, 0.3), y: cl(v.y, -0.3, 0.3), z: cl(v.z, 0, H) };
    }
  }
  return bn;
}



let seq = [];
for (let f of lm) {
  let bn = {};
  if (f.p2 && f.p3) {
    try {
      let rp = PS.solve(f.p3, f.p2, {
        runtime: 'mediapipe',
        video: { width: f.w, height: f.h }
      });
      Object.assign(bn, mpa(rp));
    } catch (e) {}
  }
  if (f.rh) {
    try { Object.assign(bn, mhd(HS.solve(f.rh, 'Right'), 'Right')); } catch (e) {}
  }
  if (f.lh) {
    try { Object.assign(bn, mhd(HS.solve(f.lh, 'Left'), 'Left')); } catch (e) {}
  }
  if (Object.keys(bn).length > 0) seq.push({ duration: DT, bones: bn });
}

console.log('\n=== Step 3: Writing output ===');

if (seq.length > 0) {
  const DEG = Math.PI / 180;
  
  let ob = {
    spine: { x: 0, y: 0, z: 0 },
    chest: { x: 0, y: 0, z: 0 },
    neck: { x: 0, y: 0, z: 0 },
    head: { x: 0, y: 0, z: 0 },
    // Your verified idle configuration
    rightUpperArm: { x: 0, y: 0, z: 70 * DEG }, 
    rightLowerArm: { x: 0, y: 0, z: 0 },
    rightHand: { x: 0, y: 0, z: 0 },
    leftUpperArm: { x: 0, y: 0, z: -70 * DEG },
    leftLowerArm: { x: 0, y: 0, z: 0 },
    leftHand: { x: 0, y: 0, z: 0 }
  };

  // Slight natural curl for the fingers
  const fRot = (ang, sd) => ({ x: 0, y: 0, z: (sd === 'R' ? ang : -ang) * DEG });
  for (const d of ['Thumb', 'Index', 'Middle', 'Ring', 'Little']) {
    for (const j of ['Proximal', 'Intermediate', 'Distal']) {
      ob['right' + d + j] = fRot(10, 'R');
      ob['left' + d + j] = fRot(10, 'L');
    }
  }
  
  seq.unshift({ duration: 0.5, bones: ob });
}

fs.writeFileSync(OT, JSON.stringify(seq, null, 2));
console.log('  ' + seq.length + ' animation frames -> ' + ph.basename(OT));

try { fs.unlinkSync(TF); } catch (e) {}
try { fs.unlinkSync(pf); } catch (e) {}
try { fs.unlinkSync(ph.join(CD, '_dl.cjs')); } catch (e) {}
console.log('Done.');
