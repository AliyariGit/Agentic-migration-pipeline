import { Component, input, output } from '@angular/core';
import { Technology } from '../../services/conversion';

@Component({
  selector: 'app-tech-card',
  imports: [],
  templateUrl: './tech-card.html',
  styleUrl: './tech-card.scss',
})
export class TechCard {
  tech     = input.required<Technology>();
  selected = input<boolean>(false);
  picked   = output<Technology>();

  select() { this.picked.emit(this.tech()); }
}
