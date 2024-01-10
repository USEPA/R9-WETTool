import {bootstrapApplication, provideProtractorTestingSupport} from '@angular/platform-browser';
import {importProvidersFrom} from '@angular/core';
import {provideHttpClient} from "@angular/common/http";
import {provideRouter} from '@angular/router';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';

import routeConfig from './app/routes';
import {AppComponent} from './app/app.component';

// if (environment.production) {
//   enableProdMode();
// }

bootstrapApplication(AppComponent,
  {
    providers: [
      provideProtractorTestingSupport(),
      provideHttpClient(),
      importProvidersFrom(BrowserAnimationsModule), //hacky!
      provideRouter(routeConfig)
    ]
  }
).catch(err => console.error(err));

// platformBrowserDynamic().bootstrapModule(AppModule)
//   .catch(err => console.error(err));
