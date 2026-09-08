import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { applyDocumentLang } from "./i18n";
import "./styles/gw2.css";

applyDocumentLang();
createApp(App).use(router).mount("#app");
