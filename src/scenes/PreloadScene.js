import Phaser from 'phaser';

const DIRECTIONS = [
  'south',
  'south-east',
  'east',
  'north-east',
  'north',
  'north-west',
  'west',
  'south-west'
];

const ANIMATED_CHARACTERS = [
  {
    key: 'cp3o',
    path: 'cp3o/animations/walking',
    frameCount: 8
  },
  {
    key: 'astromech',
    path: 'astromech/animations/sad-walk',
    frameCount: 8
  }
];

const ROTATION_CHARACTERS = [
  {
    key: 'rebelsoldier',
    path: 'rebelsoldier'
  },
  {
    key: 'gnk-droid',
    path: 'gnk-droid/rotations'
  },
  {
    key: 'golddroid',
    path: 'golddroid/rotations'
  }
];

export class PreloadScene extends Phaser.Scene {
  constructor() {
    super('Preload');
  }

  preload() {
    // Loading bar
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;
    const bar = this.add.rectangle(width / 2, height / 2, 300, 20, 0x222222);
    const fill = this.add.rectangle(width / 2 - 148, height / 2, 4, 16, 0x00ff00);

    this.load.on('progress', (value) => {
      fill.width = 296 * value;
      fill.x = width / 2 - 148 + fill.width / 2;
    });

    ANIMATED_CHARACTERS.forEach((character) => {
      DIRECTIONS.forEach((direction) => {
        for (let index = 0; index < character.frameCount; index += 1) {
          const frame = index.toString().padStart(3, '0');
          this.load.image(
            `${character.key}-${direction}-${index}`,
            `/assets/sprites/characters/${character.path}/${direction}/frame_${frame}.png`
          );
        }
      });
    });

    ROTATION_CHARACTERS.forEach((character) => {
      DIRECTIONS.forEach((direction) => {
        this.load.image(
          `${character.key}-${direction}`,
          `/assets/sprites/characters/${character.path}/${direction}.png`
        );
      });
    });
  }

  create() {
    this.scene.start('Game');
  }
}
