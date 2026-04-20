import { VRMLoaderPlugin } from '@pixiv/three-vrm';
import { Environment, OrbitControls } from '@react-three/drei';
import { Canvas, useFrame } from '@react-three/fiber';
import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

/** Smoothly slerp a VRM bone toward a target euler rotation. */
function rigRotation(vrm, boneName, euler, dampener = 0.3) {
  if (!euler) return;
  const boneNode = vrm.humanoid?.getNormalizedBoneNode(boneName);
  if (!boneNode) return;
  const targetQuat = new THREE.Quaternion().setFromEuler(
    new THREE.Euler(euler.x, euler.y, euler.z, 'XYZ')
  );
  boneNode.quaternion.slerp(targetQuat, dampener);
}

/** Snap a bone to a target euler rotation instantly (no slerp). */
function setBoneRotation(vrm, boneName, euler) {
  if (!euler) return;
  const boneNode = vrm.humanoid?.getNormalizedBoneNode(boneName);
  if (!boneNode) return;
  boneNode.rotation.set(euler.x, euler.y, euler.z, 'XYZ');
}

const ALL_REST_BONES = [
  'upperChest', 'neck', 'head',
  'leftShoulder', 'leftLowerArm', 'leftHand',
  'rightShoulder', 'rightLowerArm', 'rightHand',
  'leftUpperLeg', 'leftLowerLeg', 'leftFoot', 'leftToes',
  'rightUpperLeg', 'rightLowerLeg', 'rightFoot', 'rightToes',
  'leftThumbProximal', 'leftThumbIntermediate', 'leftThumbDistal',
  'leftIndexProximal', 'leftIndexIntermediate', 'leftIndexDistal',
  'leftMiddleProximal', 'leftMiddleIntermediate', 'leftMiddleDistal',
  'leftRingProximal', 'leftRingIntermediate', 'leftRingDistal',
  'leftLittleProximal', 'leftLittleIntermediate', 'leftLittleDistal',
  'rightThumbProximal', 'rightThumbIntermediate', 'rightThumbDistal',
  'rightIndexProximal', 'rightIndexIntermediate', 'rightIndexDistal',
  'rightMiddleProximal', 'rightMiddleIntermediate', 'rightMiddleDistal',
  'rightRingProximal', 'rightRingIntermediate', 'rightRingDistal',
  'rightLittleProximal', 'rightLittleIntermediate', 'rightLittleDistal'
];

function VRMAvatar({ vrm, animData, onSequenceEnd }) {
  const vrmRef = useRef(null);
  const animDataRef = useRef(null);
  const onSequenceEndRef = useRef(null);
  const playback = useRef({ keyIndex: 0, elapsed: 0, playing: false });

  useEffect(() => {
    animDataRef.current = animData;
    onSequenceEndRef.current = onSequenceEnd;
  });

  useEffect(() => {
    if (!vrm) return;
    vrm.scene.rotation.y = Math.PI;
    vrmRef.current = vrm;

    if (!animData || animData.length === 0) {
      console.log('VRMAvatar: Avatar transitioning to Rest Position');
      playback.current.playing = false;
      return;
    }

    console.log('VRMAvatar: Initializing gesture sequence of', animData.length, 'frames');
    const f0 = animData[0];
    if (f0) {
      const boneMap = f0.bones || f0;
      for (const [bn, eu] of Object.entries(boneMap)) {
        if (bn === 'hips' || bn === 'spine' || bn === 'chest') continue;
        setBoneRotation(vrm, bn, eu);
      }
    }
    playback.current.keyIndex = 0;
    playback.current.elapsed = 0;
    playback.current.playing = true;
  }, [vrm, animData]);

  useFrame((_state, dt) => {
    const v = vrmRef.current;
    if (!v) return;
    const pb = playback.current;
    const currentAnimData = animDataRef.current;
    
    if (pb.playing && currentAnimData) {
      if (pb.keyIndex >= currentAnimData.length) {
        pb.playing = false;
        const cb = onSequenceEndRef.current;
        if (cb) {
          console.log('VRMAvatar: Gesture sequence completed');
          cb();
        }
      } else {
        const kf = currentAnimData[pb.keyIndex];
        const dur = kf.duration || 0.1;
        const t = Math.min(pb.elapsed / dur, 1);
        const dmp = 0.15 + t * 0.25;

        const boneMap = kf.bones || kf;
        for (const [bn, eu] of Object.entries(boneMap)) {
          if (bn === 'hips' || bn === 'spine' || bn === 'chest') continue;
          rigRotation(v, bn, eu, dmp);
        }

        pb.elapsed += dt;
        if (pb.elapsed >= dur) {
          pb.elapsed = 0;
          pb.keyIndex += 1;
        }
      }
    } else {
      // Smoothly slerp all bones towards the standard rest position
      ALL_REST_BONES.forEach((bn) => {
        rigRotation(v, bn, { x: 0, y: 0, z: 0 }, 0.1);
      });
      // Enforce the relaxed A-pose for the upper arms
      rigRotation(v, 'leftUpperArm', { x: 0, y: 0, z: 1.2 }, 0.1);
      rigRotation(v, 'rightUpperArm', { x: 0, y: 0, z: -1.2 }, 0.1);
    }
    v.update(dt);
  });

  return vrm ? <primitive object={vrm.scene} /> : null;
}

export default function AvatarRenderer({ dynamicAnimData, onSequenceEnd }) {
  const [vrm, setVrm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [animData, setAnimData] = useState(null);

  useEffect(() => {
    if (dynamicAnimData && dynamicAnimData.length > 0) {
      console.log('AvatarRenderer: Received playback sequence API data');
      setAnimData(dynamicAnimData);
    } else {
      console.log('AvatarRenderer: Setting to default rest state');
      setAnimData(null);
    }
  }, [dynamicAnimData]);

  // Load VRM model
  useEffect(() => {
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));
    loader.load(
      '/models/AvatarSample_C.vrm',
      (gltf) => {
        const v = gltf.userData.vrm;
        if (!v) {
          console.error('VRM data not found in GLTF — check the model file');
          setError('Failed to parse avatar model');
          setLoading(false);
          return;
        }
        v.scene.traverse((o) => {
          o.frustumCulled = false;
        });
        setVrm(v);
        setLoading(false);
        console.log('VRM avatar loaded ✔');
      },
      (p) =>
        console.log(
          'Loading VRM…',
          ((p.loaded / p.total) * 100).toFixed(1) + '%'
        ),
      (e) => {
        console.error('VRM load error:', e);
        setError('Failed to load avatar model');
        setLoading(false);
      }
    );
  }, []);

  return (
    <div className="avatar-container">
      {loading && (
        <div className="avatar-loading">
          <div className="avatar-spinner" />
          <span>Loading avatar…</span>
        </div>
      )}
      {error && (
        <div className="avatar-error">
          <span>{error}</span>
        </div>
      )}
      <Canvas
        camera={{ position: [0, 1.2, 2.5], fov: 40 }}
        style={{ width: '100%', height: '100%' }}
      >
        <ambientLight intensity={1.2} />
        <directionalLight position={[2, 3, 4]} intensity={1.8} />
        <Environment preset="city" />
        <OrbitControls target={[0, 1.2, 0]} />
        <VRMAvatar vrm={vrm} animData={animData} onSequenceEnd={onSequenceEnd} />
      </Canvas>
    </div>
  );
}
