import { useRef, useEffect, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { VRMLoaderPlugin } from '@pixiv/three-vrm';
import * as THREE from 'three';
import FALLBACK_SEQUENCE from '../lib/animationData';

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

function VRMAvatar({ vrm, isActive, animData }) {
  const vrmRef = useRef(null);
  const playback = useRef({ keyIndex: 0, elapsed: 0, playing: false });
useEffect(() => {
    if (!vrm) return;
    vrm.scene.rotation.y = Math.PI;
    vrmRef.current = vrm;
    const f0 = animData[0];
    if (f0) {
      for (const [bn, eu] of Object.entries(f0.bones)) {
        if (bn === 'hips' || bn === 'spine' || bn === 'chest') continue;
        setBoneRotation(vrm, bn, eu);
      }
    }
  }, [vrm, animData]);

  useEffect(() => {
    const pb = playback.current;
    if (isActive) {
      pb.keyIndex = 0;
      pb.elapsed = 0;
      pb.playing = true;
    } else {
      pb.playing = false;
      if (vrmRef.current && animData[0]) {
        for (const [bn, eu] of Object.entries(animData[0].bones)) {
          if (bn === 'hips' || bn === 'spine' || bn === 'chest') continue;
          setBoneRotation(vrmRef.current, bn, eu);
        }
      }
    }
  }, [isActive, animData]);

  useFrame((_state, dt) => {
    const v = vrmRef.current;
    if (!v) return;
    const pb = playback.current;
    if (pb.playing) {
      if (pb.keyIndex >= animData.length) { 
        pb.playing = false; 
        return; 
      }
      const kf = animData[pb.keyIndex];
      const t = Math.min(pb.elapsed / kf.duration, 1);
      const dmp = 0.15 + t * 0.25;
      
      for (const [bn, eu] of Object.entries(kf.bones)) {
        if (bn === 'hips' || bn === 'spine' || bn === 'chest') continue;
        rigRotation(v, bn, eu, dmp);
      }
      
      pb.elapsed += dt;
      if (pb.elapsed >= kf.duration) { 
        pb.elapsed = 0; 
        pb.keyIndex += 1; 
      }
    }
    v.update(dt);
  });
  return vrm ? <primitive object={vrm.scene} /> : null;
}

export default function AvatarRenderer({ isActive }) {
  const [vrm, setVrm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [animData, setAnimData] = useState(FALLBACK_SEQUENCE);

  // Try to load solver output; fall back to hardcoded sequence
  useEffect(() => {
    fetch('/models/vrm_animation.json')
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          console.log('Loaded vrm_animation.json (' + data.length + ' frames)');
          setAnimData(data);
        }
      })
      .catch(() => console.log('Using fallback animation'));
  }, []);

  useEffect(() => {
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));
    loader.load(
      '/models/AvatarSample_C.vrm',
      (gltf) => {
        const v = gltf.userData.vrm;
        v.scene.traverse((o) => { o.frustumCulled = false; });
        setVrm(v);
        setLoading(false);
        console.log('VRM loaded ✔');
      },
      (p) => console.log('Loading VRM…', ((p.loaded / p.total) * 100).toFixed(1) + '%'),
      (e) => { console.error('VRM error:', e); setLoading(false); }
    );
  }, []);

  return (
    <div className="flex-[1.4] bg-white/50 backdrop-blur rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden min-h-[400px]">
      {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/70 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
            <span className="text-sm text-gray-500 font-medium">Loading avatar…</span>
          </div>
        </div>
      )}
      <Canvas
        camera={{ position: [0, 1.2, -2.5], fov: 40 }}
        style={{ width: '100%', height: '100%' }}
      >
        <ambientLight intensity={1.2} />
        <directionalLight position={[2, 3, 4]} intensity={1.8} />
        <Environment preset="city" />
        <OrbitControls target={[0, 1.2, 0]} />
        <VRMAvatar vrm={vrm} isActive={isActive} animData={animData} />
      </Canvas>
    </div>
  );
}