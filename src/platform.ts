/**
 * True inside the Windows desktop app (Tauri), false when the same UI runs as the web version
 * at lolworlds.com/riftwatch. Desktop-only features (tray, hotkey, floating HUD, Windows startup,
 * self-updater, native notifications) are hidden on the web.
 */
export const IS_DESKTOP: boolean = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
export const IS_WEB = !IS_DESKTOP;

/** Riot Games' required notice for fan projects ("Legal Jibber Jabber"), verbatim apart from the name. */
export const RIOT_LEGAL_NOTICE =
  "RiftWatch isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone " +
  "officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties " +
  "are trademarks or registered trademarks of Riot Games, Inc.";

/** Download for the desktop app. Disabled on the web page until the public release is ready. */
export const DESKTOP_DOWNLOAD_ENABLED = false;
export const DESKTOP_DOWNLOAD_URL = "https://github.com/drmonocle/riftwatch/releases/latest/download/RiftWatch.exe";
