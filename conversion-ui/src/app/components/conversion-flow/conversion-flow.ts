import { Component, inject } from '@angular/core';
import { ConversionService } from '../../services/conversion';

@Component({
  selector: 'app-conversion-flow',
  imports: [],
  templateUrl: './conversion-flow.html',
  styleUrl: './conversion-flow.scss',
})
export class ConversionFlow {
  svc = inject(ConversionService);
}
