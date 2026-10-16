// What the radar adds to the site's chrome: a desktop sidebar entry under 内容 and a phone tab.
// Icons and navigation types come from the web app; the page itself lives in web/radar-route.tsx.
import { IconChart, IconFlame } from "@aihot/web/components/icons";
import { defineWebModule } from "@aihot/web/modules";

export default defineWebModule({
  name: "short-term-radar",
  sidebar: {
    section: "内容",
    items: [{ to: "/radar", label: "短线雷达", icon: IconChart }],
  },
  tabs: [{ key: "radar", to: "/radar", label: "雷达", icon: IconFlame }],
});