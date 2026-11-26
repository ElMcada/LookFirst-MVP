import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ToastsComponent } from '@shared/ui/toasts.component';

@Component({
  selector: 'lf-root',
  imports: [RouterOutlet, ToastsComponent],
  template: `<router-outlet /><lf-toasts />`,
})
export class App {}
