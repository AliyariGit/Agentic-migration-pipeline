import { Component } from '@angular/core';
import { ConversionSelector } from './components/conversion-selector/conversion-selector';

@Component({
  selector: 'app-root',
  imports: [ConversionSelector],
  template: '<app-conversion-selector />',
})
export class App {}
