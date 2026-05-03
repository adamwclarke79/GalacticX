const directions = [
  'south',
  'south-east',
  'east',
  'north-east',
  'north',
  'north-west',
  'west',
  'south-west'
];

const animatedCharacters = [
  {
    id: 'cp3o',
    name: 'C-3PO',
    path: 'cp3o/animations/walking',
    x: 150,
    y: 355,
    scale: 2.6,
    frameCount: 8,
    frameMs: 92,
    drift: 42
  },
  {
    id: 'r2d2_replica',
    name: 'R2-D2 Replica',
    path: 'r2d2_replica/animations/rolling',
    x: 355,
    y: 355,
    scale: 2,
    frameCount: 8,
    frameMs: 96,
    drift: 24,
    anchorBottom: 82
  },
  {
    id: 'stormtrooper_gun',
    name: 'Stormtrooper',
    path: 'stormtrooper_gun/animations/walking',
    x: 650,
    y: 350,
    scale: 1.85,
    frameCount: 8,
    frameMs: 82,
    drift: 30
  }
];

const rotationCharacters = [
  {
    id: 'rebelsoldier',
    name: 'Rebel Soldier',
    path: 'rebelsoldier',
    x: 430,
    y: 520,
    scale: 1.18
  },
  {
    id: 'gnk-droid',
    name: 'GNK Droid',
    path: 'gnk-droid/rotations',
    x: 540,
    y: 520,
    scale: 1.15
  },
  {
    id: 'imperial_officer',
    name: 'Imperial Officer',
    path: 'imperial_officer/rotations',
    x: 645,
    y: 520,
    scale: 1.16
  },
  {
    id: 'golddroid',
    name: 'Gold Droid',
    path: 'golddroid/rotations',
    x: 755,
    y: 520,
    scale: 1.15
  }
];

const staticCharacters = [
  {
    id: 'stormtrooper_chest_blaster',
    name: 'Chest Blaster',
    source: 'stormtrooper_gun/api_generated/chest_blaster/stormtrooper_chest_blaster_front_smaller_gun.png',
    x: 260,
    y: 520,
    scale: 1
  }
];

const assetRoot = 'assets/sprites/characters';
const canvas = document.querySelector('#stage');
const context = canvas.getContext('2d');
const statusText = document.querySelector('[data-direction]');
const loadingText = document.querySelector('[data-loading]');
const previousButton = document.querySelector('[data-previous]');
const nextButton = document.querySelector('[data-next]');
const sprites = new Map();
const stars = Array.from({ length: 95 }, () => ({
  x: Math.random() * canvas.width,
  y: Math.random() * 285,
  r: Math.random() > 0.86 ? 2 : 1,
  alpha: 0.22 + Math.random() * 0.68,
  speed: 0.012 + Math.random() * 0.035
}));

let directionIndex = 0;
let lastDirectionChange = 0;

function spriteKey(parts) {
  return parts.join(':');
}

function loadImage(key, source) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      sprites.set(key, image);
      resolve();
    };
    image.onerror = () => reject(new Error(`Could not load ${source}`));
    image.src = source;
  });
}

async function loadSprites() {
  const jobs = [];

  animatedCharacters.forEach((character) => {
    directions.forEach((direction) => {
      for (let index = 0; index < character.frameCount; index += 1) {
        const frame = index.toString().padStart(3, '0');
        jobs.push(loadImage(
          spriteKey([character.id, direction, index]),
          `${assetRoot}/${character.path}/${direction}/frame_${frame}.png`
        ));
      }
    });
  });

  rotationCharacters.forEach((character) => {
    directions.forEach((direction) => {
      jobs.push(loadImage(
        spriteKey([character.id, direction]),
        `${assetRoot}/${character.path}/${direction}.png`
      ));
    });
  });

  staticCharacters.forEach((character) => {
    jobs.push(loadImage(
      spriteKey([character.id]),
      `${assetRoot}/${character.source}`
    ));
  });

  await Promise.all(jobs);
}

function drawBackdrop(time) {
  const sky = context.createLinearGradient(0, 0, 0, 380);
  sky.addColorStop(0, '#070a15');
  sky.addColorStop(0.62, '#111827');
  sky.addColorStop(1, '#202638');
  context.fillStyle = sky;
  context.fillRect(0, 0, canvas.width, canvas.height);

  stars.forEach((star) => {
    const shimmer = 0.55 + Math.sin(time * star.speed + star.x) * 0.35;
    context.globalAlpha = star.alpha * shimmer;
    context.fillStyle = '#ffffff';
    context.fillRect(star.x, star.y, star.r, star.r);
  });
  context.globalAlpha = 1;

  context.fillStyle = '#294c73';
  context.beginPath();
  context.arc(105, 112, 44, 0, Math.PI * 2);
  context.fill();
  context.strokeStyle = 'rgba(135, 216, 255, 0.4)';
  context.lineWidth = 3;
  context.stroke();
  context.fillStyle = 'rgba(90, 167, 184, 0.8)';
  context.beginPath();
  context.arc(88, 98, 12, 0, Math.PI * 2);
  context.fill();
  context.fillStyle = 'rgba(19, 43, 70, 0.45)';
  context.beginPath();
  context.arc(124, 126, 16, 0, Math.PI * 2);
  context.fill();

  context.fillStyle = '#171a25';
  context.fillRect(0, 374, canvas.width, 226);
  context.fillStyle = '#3c465d';
  context.fillRect(0, 372, canvas.width, 8);

  context.strokeStyle = 'rgba(72, 84, 112, 0.55)';
  context.lineWidth = 1;
  for (let x = 0; x <= canvas.width; x += 40) {
    context.beginPath();
    context.moveTo(x, 380);
    context.lineTo(x - 65, canvas.height);
    context.stroke();
  }
  for (let y = 392; y <= canvas.height; y += 36) {
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(canvas.width, y);
    context.stroke();
  }
}

function drawText(text, x, y, options = {}) {
  context.font = `${options.size || 16}px Consolas, Monaco, monospace`;
  context.textAlign = options.align || 'left';
  context.textBaseline = options.baseline || 'top';
  context.fillStyle = options.color || '#ffffff';
  context.fillText(text, x, y);
}

function drawNameplate(text, x, y) {
  context.font = '13px Consolas, Monaco, monospace';
  const width = Math.ceil(context.measureText(text).width) + 16;
  context.fillStyle = 'rgba(9, 14, 26, 0.88)';
  context.strokeStyle = 'rgba(130, 160, 210, 0.5)';
  context.lineWidth = 1;
  context.fillRect(x - width / 2, y, width, 24);
  context.strokeRect(x - width / 2, y, width, 24);
  drawText(text, x, y + 5, {
    size: 13,
    align: 'center',
    color: '#dce8ff'
  });
}

function drawSprite(image, x, y, scale, anchorBottom = image.height) {
  const width = image.width * scale;
  const height = image.height * scale;
  context.imageSmoothingEnabled = false;
  context.drawImage(image, Math.round(x - width / 2), Math.round(y - anchorBottom * scale), width, height);
}

function drawCharacters(time) {
  const direction = directions[directionIndex];

  animatedCharacters.forEach((character, characterIndex) => {
    const frame = Math.floor(time / character.frameMs) % character.frameCount;
    const image = sprites.get(spriteKey([character.id, direction, frame]));
    const drift = Math.sin(time / 520 + characterIndex) * character.drift;
    drawSprite(image, character.x + drift, character.y, character.scale, character.anchorBottom);
    drawNameplate(character.name, character.x, character.y + 28);
  });

  rotationCharacters.forEach((character, characterIndex) => {
    const image = sprites.get(spriteKey([character.id, direction]));
    const bob = Math.sin(time / (620 + characterIndex * 80)) * 8;
    drawSprite(image, character.x, character.y + bob, character.scale);
    drawNameplate(character.name, character.x, character.y + 28);
  });

  staticCharacters.forEach((character) => {
    const image = sprites.get(spriteKey([character.id]));
    drawSprite(image, character.x, character.y, character.scale);
    drawNameplate(character.name, character.x, character.y + 28);
  });
}

function drawScene(time) {
  drawBackdrop(time);
  drawText('GalacticX Sprite Bay', 32, 26, { size: 30, color: '#ffe81f' });
  drawText('Live animation built from the repository character sprites', 34, 66, {
    size: 14,
    color: '#b9c7df'
  });
  drawCharacters(time);
}

function setDirection(index) {
  directionIndex = (index + directions.length) % directions.length;
  statusText.textContent = `Facing ${directions[directionIndex].replace('-', ' ')}`;
}

function animate(time) {
  if (time - lastDirectionChange > 1600) {
    setDirection(directionIndex + 1);
    lastDirectionChange = time;
  }

  drawScene(time);
  requestAnimationFrame(animate);
}

previousButton.addEventListener('click', () => {
  setDirection(directionIndex - 1);
  lastDirectionChange = performance.now();
});

nextButton.addEventListener('click', () => {
  setDirection(directionIndex + 1);
  lastDirectionChange = performance.now();
});

loadSprites()
  .then(() => {
    loadingText.hidden = true;
    setDirection(0);
    requestAnimationFrame(animate);
  })
  .catch((error) => {
    loadingText.textContent = error.message;
  });
