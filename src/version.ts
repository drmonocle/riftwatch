import pkg from "../package.json";

/** Single source of truth for the version shown in the UI (comes from package.json). */
export const APP_VERSION: string = pkg.version;
