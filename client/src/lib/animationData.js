/**
 * Procedurally generated ISL-like animation keyframes.
 * Focused on isolating explicitly visible finger movement.
 */

const DEG = Math.PI / 180;
const rot = (x = 0, y = 0, z = 0) => ({ x: x * DEG, y: y * DEG, z: z * DEG });

// Helper to handle standard VRM finger curls
const fRot = (ang, sd) => {
  const val = sd === 'right' ? -ang : ang;
  // If fingers spread sideways instead of curling inward, change to: rot(val, 0, 0)
  return rot(0, 0, val); 
};

// Helper to generate full hand poses
const getHnd = (sd, st) => {
  const res = {};
  const setDgt = (nm, p, i, d) => {
    res[sd + nm + 'Proximal'] = fRot(p, sd);
    res[sd + nm + 'Intermediate'] = fRot(i, sd);
    res[sd + nm + 'Distal'] = fRot(d, sd);
  };

  if (st === 'rel') {
    // Relaxed neutral hand
    setDgt('Thumb', 10, 10, 10);
    setDgt('Index', 15, 15, 15);
    setDgt('Middle', 20, 20, 20);
    setDgt('Ring', 25, 25, 25);
    setDgt('Little', 30, 30, 30);
  } else if (st === 'fist') {
    // Tight fist
    setDgt('Thumb', 50, 50, 50);
    setDgt('Index', 80, 80, 80);
    setDgt('Middle', 80, 80, 80);
    setDgt('Ring', 80, 80, 80);
    setDgt('Little', 80, 80, 80);
  } else if (st === 'one') {
    // Index finger up
    setDgt('Thumb', 50, 50, 50);
    setDgt('Index', 0, 0, 0);
    setDgt('Middle', 80, 80, 80);
    setDgt('Ring', 80, 80, 80);
    setDgt('Little', 80, 80, 80);
  } else if (st === 'two') {
    // Index and Middle up
    setDgt('Thumb', 50, 50, 50);
    setDgt('Index', 0, 0, 0);
    setDgt('Middle', 0, 0, 0);
    setDgt('Ring', 80, 80, 80);
    setDgt('Little', 80, 80, 80);
  } else if (st === 'three') {
    // Index, Middle, and Ring up
    setDgt('Thumb', 50, 50, 50);
    setDgt('Index', 0, 0, 0);
    setDgt('Middle', 0, 0, 0);
    setDgt('Ring', 0, 0, 0);
    setDgt('Little', 80, 80, 80);
  } else if (st === 'four') {
    // All fingers up, thumb tucked
    setDgt('Thumb', 50, 50, 50);
    setDgt('Index', 0, 0, 0);
    setDgt('Middle', 0, 0, 0);
    setDgt('Ring', 0, 0, 0);
    setDgt('Little', 0, 0, 0);
  } else if (st === 'five') {
    // Fully open hand
    setDgt('Thumb', 0, 0, 0);
    setDgt('Index', 0, 0, 0);
    setDgt('Middle', 0, 0, 0);
    setDgt('Ring', 0, 0, 0);
    setDgt('Little', 0, 0, 0);
  }
  return res;
};

export const COUNT_ANIMATION = [
  // ─── 1. Idle / Arms at sides ───
  {
    duration: 0.6,
    bones: {
      spine:            rot(0, 0, 0),
      chest:            rot(0, 0, 0),
      neck:             rot(0, 0, 0),
      head:             rot(0, 0, 0),
      rightUpperArm:    rot(0, 0, -70),      
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, 0),
      leftUpperArm:     rot(0, 0, 70),     
      leftLowerArm:     rot(0, 0, 0),
      leftHand:         rot(0, 0, 0),
      ...getHnd('right', 'rel'),
      ...getHnd('left', 'rel')
    },
  },

  // ─── 2. Raise Right Arm and form a FIST ───
  {
    duration: 0.5,
    bones: {
      rightUpperArm:    rot(0, 45, 50),     // Arm forward and slightly up
      rightLowerArm:    rot(0, 100, 0),     // Bent so hand is in front of chest
      rightHand:        rot(0, -90, 30),
      ...getHnd('right', 'fist'),           // Form tight fist
    },
  },

  // ─── 3. Count "ONE" ───
  {
    duration: 0.6,
    bones: {
      rightUpperArm:    rot(0, 45, 50),     
      rightLowerArm:    rot(0, 100, 0),     
      rightHand:        rot(0, -90, 30), 
      ...getHnd('right', 'one'),            // Index finger straightens
    },
  },

  // ─── 4. Count "TWO" ───
  {
    duration: 0.6,
    bones: {
      rightUpperArm:    rot(0, 45, 50),     
      rightLowerArm:    rot(0, 100, 0),     
      rightHand:        rot(0, -90, 30), 
      ...getHnd('right', 'two'),            // Middle finger straightens
    },
  },

  // ─── 5. Count "THREE" ───
  {
    duration: 0.6,
    bones: {
      rightUpperArm:    rot(0, 45, 50),     
      rightLowerArm:    rot(0, 100, 0),     
      rightHand:        rot(0, -90, 30), 
      ...getHnd('right', 'three'),          // Ring finger straightens
    },
  },

  // ─── 6. Count "FOUR" ───
  {
    duration: 0.6,
    bones: {
      rightUpperArm:    rot(0, 45, 50),     
      rightLowerArm:    rot(0, 100, 0),     
      rightHand:        rot(0, -90, 30), 
      ...getHnd('right', 'four'),           // Pinky straightens
    },
  },

  // ─── 7. Count "FIVE" (Open Palm) ───
  {
    duration: 0.8,
    bones: {
      rightUpperArm:    rot(0, 45, 50),     
      rightLowerArm:    rot(0, 100, 0),     
      rightHand:        rot(0, -90, 30), 
      ...getHnd('right', 'five'),           // Thumb opens
    },
  },

  // ─── 8. Final Rest ───
  {
    duration: 0.8,
    bones: {
      spine:            rot(0, 0, 0),
      chest:            rot(0, 0, 0),
      neck:             rot(0, 0, 0),
      head:             rot(0, 0, 0),
      rightUpperArm:    rot(0, 0, -70),      
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, 0),
      leftUpperArm:     rot(0, 0, 70),     
      leftLowerArm:     rot(0, 0, 0),
      leftHand:         rot(0, 0, 0),
      ...getHnd('right', 'rel'),
      ...getHnd('left', 'rel')
    },
  },
];


// --- 🌟 NAMASTE ANIMATION ---
export const NAMASTE_ANIMATION = [
  {
    duration: 0.6,
    bones: {
      spine:            rot(0, 0, 0),
      chest:            rot(0, 0, 0),
      neck:             rot(0, 0, 0),
      head:             rot(0, 0, 0),
      rightUpperArm:    rot(0, 0, -70),      
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, 0),
      leftUpperArm:     rot(0, 0, 70),     
      leftLowerArm:     rot(0, 0, 0),
      leftHand:         rot(0, 0, 0),
      ...getHnd('right', 'rel'),
      ...getHnd('left', 'rel')
    },
  },
  {
    duration: 1.0,
    bones: {
      spine:            rot(0, 0, 0),
      chest:            rot(10, 0, 0),     // Lean forward slightly
      head:             rot(15, 0, 0),     // Bow head forward slightly
      rightUpperArm:    rot(-40, -20, 20), // Swing arm forward and in 
      rightLowerArm:    rot(-90, 0, 0),    // Bend elbow upward across chest
      rightHand:        rot(0, 0, 0),      // Keep wrist flat
      leftUpperArm:     rot(-40, 20, -20), // Swing left arm forward and in
      leftLowerArm:     rot(-90, 0, 0),    // Bend left elbow upward
      leftHand:         rot(0, 0, 0),      // Keep wrist flat
      ...getHnd('right', 'five'),          // Straight open hand
      ...getHnd('left', 'five'),           // Straight open hand
    },
  },
  {
    duration: 1.5, // Hold pose
    bones: {
      spine:            rot(0, 0, 0),
      chest:            rot(10, 0, 0),
      head:             rot(15, 0, 0),
      rightUpperArm:    rot(-40, -20, 20),
      rightLowerArm:    rot(-90, 0, 0),
      rightHand:        rot(0, 0, 0),
      leftUpperArm:     rot(-40, 20, -20),
      leftLowerArm:     rot(-90, 0, 0),
      leftHand:         rot(0, 0, 0),
      ...getHnd('right', 'five'),
      ...getHnd('left', 'five'),
    },
  },
  {
    duration: 0.8, // Final Rest
    bones: {
      spine:            rot(0, 0, 0),
      chest:            rot(0, 0, 0),
      head:             rot(0, 0, 0),
      rightUpperArm:    rot(0, 0, -70),
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, 0),
      leftUpperArm:     rot(0, 0, 70),
      leftLowerArm:     rot(0, 0, 0),
      leftHand:         rot(0, 0, 0),
      ...getHnd('right', 'rel'),
      ...getHnd('left', 'rel')
    },
  }
];

// --- 🌟 FULL BODY WAVE ANIMATION ---
export const WAVE_ANIMATION = [
  {
    duration: 0.6,
    bones: {
      spine:            rot(0, 0, 0),
      chest:            rot(0, 0, 0),
      neck:             rot(0, 0, 0),
      head:             rot(0, 0, 0),
      rightUpperArm:    rot(0, 0, -70),      
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, 0),
      leftUpperArm:     rot(0, 0, 70),     
      leftLowerArm:     rot(0, 0, 0),
      leftHand:         rot(0, 0, 0),
      ...getHnd('right', 'rel'),
      ...getHnd('left', 'rel')
    },
  },
  {
    duration: 0.5,
    bones: { // Raise arm
      rightUpperArm:    rot(-10, 0, 160),  // Hand straight up alongside ear
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, 0),
      ...getHnd('right', 'five'),
    },
  },
  { // Wave left
    duration: 0.3,
    bones: {
      rightUpperArm:    rot(-10, 0, 160),
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, -30),    // Oscillate wrist on Z axis
      ...getHnd('right', 'five'),
    },
  },
  { // Wave right
    duration: 0.3,
    bones: {
      rightUpperArm:    rot(-10, 0, 160),
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, 30),     // Oscillate wrist on Z axis
      ...getHnd('right', 'five'),
    },
  },
  { // Wave left
    duration: 0.3,
    bones: {
      rightUpperArm:    rot(-10, 0, 160),
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, -30),
      ...getHnd('right', 'five'),
    },
  },
  { // Wave right
    duration: 0.3,
    bones: {
      rightUpperArm:    rot(-10, 0, 160),
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, 30),
      ...getHnd('right', 'five'),
    },
  },
  { // Drop
    duration: 0.6,
    bones: {
      rightUpperArm:    rot(0, 0, -70),
      rightLowerArm:    rot(0, 0, 0),
      rightHand:        rot(0, 0, 0),
      ...getHnd('right', 'rel'),
    },
  }
];
