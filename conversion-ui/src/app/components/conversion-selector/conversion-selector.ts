import { Component, inject } from '@angular/core';
import { ConversionService, SOURCE_TECHNOLOGIES, TARGET_TECHNOLOGIES, Technology } from '../../services/conversion';
import { TechCard } from '../tech-card/tech-card';
import { ConversionFlow } from '../conversion-flow/conversion-flow';

@Component({
  selector: 'app-conversion-selector',
  imports: [TechCard, ConversionFlow],
  templateUrl: './conversion-selector.html',
  styleUrl: './conversion-selector.scss',
})
export class ConversionSelector {
  svc = inject(ConversionService);

  sources = SOURCE_TECHNOLOGIES;
  targets = TARGET_TECHNOLOGIES;

  pickSource(tech: Technology) {
    this.svc.selectSource(tech);
  }

  pickTarget(tech: Technology) {
    this.svc.selectTarget(tech);
  }

  isSourceSelected(tech: Technology) {
    return this.svc.selectedSource()?.id === tech.id;
  }

  isTargetSelected(tech: Technology) {
    return this.svc.selectedTarget()?.id === tech.id;
  }

  startMigration() {
    // In production: POST to /api/run with source+target config
    alert(`🚀 Pipeline launched!\n\nSource: ${this.svc.selectedSource()?.label}\nTarget: ${this.svc.selectedTarget()?.label}\n\nIn production this triggers run_pipeline.py with the selected conversion config.`);
  }
}
