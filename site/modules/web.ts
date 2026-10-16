// What the site's modules add to the web pages (site/modules/index.ts).
import type { WebModule } from "@aihot/web/modules";
import shortTermRadar from "@aihot/short-term-radar/web";

export const WEB_MODULES: readonly WebModule[] = [shortTermRadar];
