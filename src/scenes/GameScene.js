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

const WALKERS = [
  {
    key: 'cp3o',
    label: 'C-3PO',
    x: 165,
    y: 345,
    scale: 2.5,
    speed: 12
  },
  {
    key: 'astromech',
    label: 'Astromech',
    x: 415,
    y: 345,
    scale: 2.35,
    speed: 10
  }
];

const ROTATORS = [
  {
    key: 'rebelsoldier',
    label: 'Rebel Soldier',
    x: 640,
    y: 335,
    scale: 1.65
  },
  {
    key: 'gnk-droid',
    label: 'GNK Droid',
    x: 535,
    y: 450,
    scale: 1.45
  },
  {
    key: 'golddroid',
    label: 'Gold Droid',
    x: 710,
    y: 450,
    scale: 1.45
  }
];

export class GameScene extends Phaser.Scene {
  constructor() {
    super('Game');
    this.directionIndex = 0;
    this.walkers = [];
    this.rotators = [];
  }

  create() {
    this.createBackdrop();
    this.createAnimations();
    this.createCharacters();
    this.createInterface();

    this.time.addEvent({
      delay: 1250,
      loop: true,
      callback: () => this.changeDirection(1)
    });
  }

  update(time) {
    this.walkers.forEach(({ sprite, baseX }, index) => {
      sprite.x = baseX + Math.sin(time / 520 + index) * 42;
    });
  }

  createBackdrop() {
    this.add.rectangle(400, 300, 800, 600, 0x090b16);

    for (let i = 0; i < 85; i += 1) {
      const x = Phaser.Math.Between(10, 790);
      const y = Phaser.Math.Between(12, 270);
      const alpha = Phaser.Math.FloatBetween(0.25, 0.9);
      this.add.circle(x, y, Phaser.Math.Between(1, 2), 0xffffff, alpha);
    }

    const planet = this.add.circle(100, 112, 42, 0x294c73, 1);
    this.add.circle(84, 98, 12, 0x5aa7b8, 0.8);
    this.add.circle(118, 125, 16, 0x132b46, 0.45);
    planet.setStrokeStyle(3, 0x87d8ff, 0.35);

    this.add.rectangle(400, 470, 820, 260, 0x171a25);
    this.add.rectangle(400, 374, 820, 10, 0x3c465d);
    this.add.grid(400, 470, 840, 250, 40, 40, 0x202638, 1, 0x343d52, 0.45);

    this.add.text(32, 28, 'GalacticX Sprite Bay', {
      fontSize: '30px',
      fontFamily: 'monospace',
      color: '#FFE81F'
    });

    this.add.text(34, 65, 'Live animations built from the repository character sprites', {
      fontSize: '14px',
      fontFamily: 'monospace',
      color: '#b9c7df'
    });
  }

  createAnimations() {
    WALKERS.forEach((character) => {
      DIRECTIONS.forEach((direction) => {
        this.anims.create({
          key: `${character.key}-${direction}-walk`,
          frames: Array.from({ length: 8 }, (_, index) => ({
            key: `${character.key}-${direction}-${index}`
          })),
          frameRate: character.speed,
          repeat: -1
        });
      });
    });
  }

  createCharacters() {
    WALKERS.forEach((character) => {
      const sprite = this.add
        .sprite(character.x, character.y, `${character.key}-south-0`)
        .setScale(character.scale)
        .setOrigin(0.5, 1);

      sprite.play(`${character.key}-south-walk`);
      this.walkers.push({ ...character, sprite, baseX: character.x });
      this.addNameplate(character.x, character.y + 28, character.label);
    });

    ROTATORS.forEach((character, index) => {
      const sprite = this.add
        .sprite(character.x, character.y, `${character.key}-south`)
        .setScale(character.scale)
        .setOrigin(0.5, 1);

      this.tweens.add({
        targets: sprite,
        y: sprite.y - 8,
        duration: 900 + index * 120,
        yoyo: true,
        repeat: -1,
        ease: 'Sine.inOut'
      });

      this.rotators.push({ ...character, sprite });
      this.addNameplate(character.x, character.y + 28, character.label);
    });
  }

  createInterface() {
    this.directionText = this.add.text(400, 116, '', {
      fontSize: '18px',
      fontFamily: 'monospace',
      color: '#ffffff',
      align: 'center'
    }).setOrigin(0.5);

    this.addButton(305, 158, '<', () => this.changeDirection(-1));
    this.addButton(495, 158, '>', () => this.changeDirection(1));

    this.add.text(400, 158, 'direction', {
      fontSize: '13px',
      fontFamily: 'monospace',
      color: '#9fb2d4'
    }).setOrigin(0.5);

    this.setDirection(0);
  }

  addButton(x, y, label, callback) {
    const button = this.add.container(x, y);
    const background = this.add.rectangle(0, 0, 52, 36, 0x24324a)
      .setStrokeStyle(2, 0x7fa8d8);
    const text = this.add.text(0, -1, label, {
      fontSize: '20px',
      fontFamily: 'monospace',
      color: '#ffffff'
    }).setOrigin(0.5);

    button.add([background, text]);
    button.setSize(52, 36);
    button.setInteractive({ useHandCursor: true });
    button.on('pointerdown', callback);
    button.on('pointerover', () => background.setFillStyle(0x32476a));
    button.on('pointerout', () => background.setFillStyle(0x24324a));
  }

  addNameplate(x, y, label) {
    this.add.text(x, y, label, {
      fontSize: '13px',
      fontFamily: 'monospace',
      color: '#dce8ff',
      backgroundColor: '#101522',
      padding: { x: 7, y: 4 }
    }).setOrigin(0.5);
  }

  changeDirection(step) {
    const nextIndex = Phaser.Math.Wrap(this.directionIndex + step, 0, DIRECTIONS.length);
    this.setDirection(nextIndex);
  }

  setDirection(index) {
    this.directionIndex = index;
    const direction = DIRECTIONS[index];
    const displayDirection = direction.replace('-', ' ');

    this.directionText.setText(`Facing ${displayDirection}`);

    this.walkers.forEach(({ key, sprite }) => {
      sprite.play(`${key}-${direction}-walk`, true);
    });

    this.rotators.forEach(({ key, sprite }) => {
      sprite.setTexture(`${key}-${direction}`);
    });
  }
}
