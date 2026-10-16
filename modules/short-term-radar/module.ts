// What the module says about its addresses: the /radar page and the api paths behind it.
// The site lists it in site/modules/index.ts; the web build reads this file to wire the route.
import { defineModule } from "@aihot/contracts/modules";

export default defineModule({
  name: "short-term-radar",
  // Beside the engine's pages, before the admin's routes.
  pages: [{ path: "radar", file: "web/radar-route.tsx", id: "short-term-radar" }],
  // The api answers these; the web server and the internal router send them to the module.
  apiPaths: [/^\/api\/(?:site|v1)\/radar(?:\/|$)/],
});