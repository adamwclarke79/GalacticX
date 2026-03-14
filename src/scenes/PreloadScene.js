import Phaser from 'phaser';

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

    // Load game assets here
  }

  create() {
    this.scene.start('Game');
  }
}
