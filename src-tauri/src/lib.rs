use std::sync::atomic::{AtomicBool, Ordering};
use tauri::{
    menu::{Menu, MenuItem, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Manager,
};
use tauri_plugin_opener::OpenerExt;

#[tauri::command]
fn start_window_drag(window: tauri::WebviewWindow) {
    let _ = window.start_dragging();
}

#[tauri::command]
fn show_ticker(app: tauri::AppHandle) {
    if let Some(w) = app.get_webview_window("ticker") {
        let _ = w.show();
        let _ = w.set_focus();
    }
}

#[tauri::command]
fn hide_ticker(app: tauri::AppHandle) {
    if let Some(w) = app.get_webview_window("ticker") {
        let _ = w.hide();
    }
}

#[tauri::command]
fn set_ticker_topmost(app: tauri::AppHandle, topmost: bool) {
    if let Some(w) = app.get_webview_window("ticker") {
        let _ = w.set_always_on_top(topmost);
    }
}

#[tauri::command]
fn show_main(app: tauri::AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

#[tauri::command]
fn quit_app(app: tauri::AppHandle) {
    app.exit(0);
}

/// Shows a native desktop notification (used for kickoff / pre-match / banger alerts).
#[tauri::command]
fn send_notification(app: tauri::AppHandle, title: String, body: String) {
    use tauri_plugin_notification::NotificationExt;
    let _ = app.notification().builder().title(title).body(body).show();
}

/// Adds or removes RiftWatch from the current user's Windows startup list (no admin needed).
#[tauri::command]
fn set_autostart(enabled: bool) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        const RUN_KEY: &str = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run";

        let mut cmd = std::process::Command::new("reg");
        if enabled {
            let exe = std::env::current_exe().map_err(|e| e.to_string())?;
            let value = format!("\"{}\" --minimized", exe.display());
            cmd.args(["add", RUN_KEY, "/v", "RiftWatch", "/t", "REG_SZ", "/d", &value, "/f"]);
        } else {
            cmd.args(["delete", RUN_KEY, "/v", "RiftWatch", "/f"]);
        }
        let status = cmd
            .creation_flags(CREATE_NO_WINDOW)
            .status()
            .map_err(|e| e.to_string())?;
        // Deleting a value that isn't there reports failure; that's fine.
        if enabled && !status.success() {
            return Err("Could not add RiftWatch to Windows startup".into());
        }
    }
    #[cfg(not(target_os = "windows"))]
    {
        let _ = enabled;
    }
    Ok(())
}

/// Whether closing the main window hides it to the tray (true) or quits the app (false).
static CLOSE_TO_TRAY: AtomicBool = AtomicBool::new(true);

#[tauri::command]
fn set_close_to_tray(enabled: bool) {
    CLOSE_TO_TRAY.store(enabled, Ordering::Relaxed);
}

/// Opens a web link in the user's default browser. Only plain http/https links are allowed.
fn open_url_checked(app: &tauri::AppHandle, url: &str) -> bool {
    let lower = url.trim().to_ascii_lowercase();
    if !(lower.starts_with("https://") || lower.starts_with("http://")) {
        return false;
    }
    app.opener().open_url(url.trim(), None::<&str>).is_ok()
}

#[tauri::command]
fn open_external_url(app: tauri::AppHandle, url: String) -> Result<(), String> {
    if open_url_checked(&app, &url) {
        Ok(())
    } else {
        Err("Blocked: only http/https links can be opened".into())
    }
}

#[tauri::command]
fn apply_app_update(app: tauri::AppHandle, download_url: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        use std::process::Command;
        use std::os::windows::process::CommandExt;

        // Security check: Only allow downloads from official repository releases
        if !download_url.starts_with("https://github.com/drmonocle/riftwatch/releases/") {
            return Err("Invalid update source URL. Only official GitHub releases are allowed.".into());
        }

        let current_exe = std::env::current_exe().map_err(|e| format!("Failed to locate current executable: {}", e))?;
        let pid = std::process::id();

        let temp_dir = std::env::temp_dir();
        let new_exe = temp_dir.join("RiftWatch_update.exe");

        const CREATE_NO_WINDOW: u32 = 0x08000000;
        const DETACHED_PROCESS: u32 = 0x00000008;

        // Download via Windows native curl.exe with -L for redirects
        let curl_status = Command::new("curl.exe")
            .args(["-L", "-s", "-S", "-f", "-o", new_exe.to_str().unwrap(), &download_url])
            .creation_flags(CREATE_NO_WINDOW)
            .status()
            .map_err(|e| format!("Failed to run download helper: {}", e))?;

        if !curl_status.success() {
            return Err("Failed to download update binary. Check your network connection.".into());
        }

        if let Ok(meta) = std::fs::metadata(&new_exe) {
            if meta.len() < 500_000 {
                return Err("Downloaded update file is invalid or truncated.".into());
            }
        } else {
            return Err("Downloaded update file not found on disk.".into());
        }

        let script_path = temp_dir.join("riftwatch_apply_update.cmd");
        let current_exe_str = current_exe.to_str().unwrap();
        let new_exe_str = new_exe.to_str().unwrap();

        let script_content = format!(
            "@echo off\r\n\
setlocal\r\n\
set \"OLD_PID={pid}\"\r\n\
set \"TARGET={current_exe_str}\"\r\n\
set \"SOURCE={new_exe_str}\"\r\n\
\r\n\
for /l %%i in (1,1,20) do (\r\n\
    tasklist /fi \"PID eq %OLD_PID%\" 2>nul | findstr \"%OLD_PID%\" >nul\r\n\
    if errorlevel 1 goto :SWAP\r\n\
    timeout /t 1 /nobreak >nul\r\n\
)\r\n\
\r\n\
:SWAP\r\n\
powershell -NoProfile -Command \"Unblock-File -LiteralPath '%SOURCE%'\" 2>nul\r\n\
\r\n\
for /l %%i in (1,1,10) do (\r\n\
    move /y \"%TARGET%\" \"%TARGET%.bak\" >nul 2>nul\r\n\
    copy /y \"%SOURCE%\" \"%TARGET%\" >nul 2>nul\r\n\
    if exist \"%TARGET%\" (\r\n\
        del /f /q \"%TARGET%.bak\" >nul 2>nul\r\n\
        del /f /q \"%SOURCE%\" >nul 2>nul\r\n\
        goto :LAUNCH\r\n\
    )\r\n\
    timeout /t 1 /nobreak >nul\r\n\
)\r\n\
\r\n\
if not exist \"%TARGET%\" if exist \"%TARGET%.bak\" move /y \"%TARGET%.bak\" \"%TARGET%\" >nul 2>nul\r\n\
goto :DONE\r\n\
\r\n\
:LAUNCH\r\n\
start \"\" \"%TARGET%\"\r\n\
\r\n\
:DONE\r\n\
del /f /q \"%~f0\" >nul 2>nul\r\n\
exit\r\n",
            pid = pid,
            current_exe_str = current_exe_str,
            new_exe_str = new_exe_str
        );

        std::fs::write(&script_path, script_content).map_err(|e| format!("Failed to write update script: {}", e))?;

        Command::new("cmd.exe")
            .args(["/c", script_path.to_str().unwrap()])
            .creation_flags(CREATE_NO_WINDOW | DETACHED_PROCESS)
            .spawn()
            .map_err(|e| format!("Failed to start update helper: {}", e))?;

        app.exit(0);
        Ok(())
    }
    #[cfg(not(target_os = "windows"))]
    {
        Err("Auto-update is currently supported on Windows only.".into())
    }
}

#[cfg(target_os = "windows")]
fn is_another_instance_running() -> bool {
    use std::ffi::OsStr;
    use std::os::windows::ffi::OsStrExt;

    extern "system" {
        fn CreateMutexW(
            lpMutexAttributes: *mut std::ffi::c_void,
            bInitialOwner: i32,
            lpName: *const u16,
        ) -> *mut std::ffi::c_void;
        fn GetLastError() -> u32;
        fn FindWindowW(lpClassName: *const u16, lpWindowName: *const u16) -> *mut std::ffi::c_void;
        fn ShowWindow(hWnd: *mut std::ffi::c_void, nCmdShow: i32) -> i32;
        fn SetForegroundWindow(hWnd: *mut std::ffi::c_void) -> i32;
    }
    const ERROR_ALREADY_EXISTS: u32 = 183;
    const SW_RESTORE: i32 = 9;

    let mutex_name: Vec<u16> = OsStr::new("Local\\RiftWatchSingleInstance")
        .encode_wide()
        .chain(std::iter::once(0))
        .collect();

    let handle = unsafe { CreateMutexW(std::ptr::null_mut(), 0, mutex_name.as_ptr()) };
    if handle.is_null() {
        return false;
    }
    if unsafe { GetLastError() } == ERROR_ALREADY_EXISTS {
        let win_title: Vec<u16> = OsStr::new("RiftWatch")
            .encode_wide()
            .chain(std::iter::once(0))
            .collect();
        let hwnd = unsafe { FindWindowW(std::ptr::null(), win_title.as_ptr()) };
        if !hwnd.is_null() {
            unsafe {
                ShowWindow(hwnd, SW_RESTORE);
                SetForegroundWindow(hwnd);
            }
        }
        return true;
    }
    false
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    #[cfg(target_os = "windows")]
    if is_another_instance_running() {
        return;
    }

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_notification::init())
        .invoke_handler(tauri::generate_handler![
            show_ticker,
            hide_ticker,
            set_ticker_topmost,
            start_window_drag,
            show_main,
            quit_app,
            open_external_url,
            set_close_to_tray,
            send_notification,
            set_autostart,
            apply_app_update
        ])
        .setup(|app| {
            // Launched by "Start with Windows": stay quietly in the tray
            if std::env::args().any(|a| a == "--minimized") {
                if let Some(w) = app.get_webview_window("main") {
                    let _ = w.hide();
                }
            }
            let show_i = MenuItem::with_id(app, "show", "Open RiftWatch", true, None::<&str>)?;
            let hide_i = MenuItem::with_id(app, "hide", "Hide to Tray", true, None::<&str>)?;
            let sep1 = PredefinedMenuItem::separator(app)?;

            let nav_live = MenuItem::with_id(app, "nav_live", "🔴 Live Matches", true, None::<&str>)?;
            let nav_schedule = MenuItem::with_id(app, "nav_schedule", "📅 Schedule & Results", true, None::<&str>)?;
            let nav_stream = MenuItem::with_id(app, "nav_stream", "📺 24/7 Stream Marathon", true, None::<&str>)?;
            let nav_watchlist = MenuItem::with_id(app, "nav_watchlist", "⭐ Watchlist & Teams", true, None::<&str>)?;
            let nav_news = MenuItem::with_id(app, "nav_news", "📰 News & Intel", true, None::<&str>)?;
            let nav_settings = MenuItem::with_id(app, "nav_settings", "⚙ Settings", true, None::<&str>)?;
            let sep2 = PredefinedMenuItem::separator(app)?;

            let toggle_hud = MenuItem::with_id(app, "toggle_hud", "📌 Toggle Desktop HUD", true, None::<&str>)?;
            let sep3 = PredefinedMenuItem::separator(app)?;

            let stream_twitch = MenuItem::with_id(app, "stream_twitch", "▶ Watch 24/7 on Twitch", true, None::<&str>)?;
            let stream_youtube = MenuItem::with_id(app, "stream_youtube", "▶ Watch 24/7 on YouTube", true, None::<&str>)?;
            let stream_sched = MenuItem::with_id(app, "stream_sched", "🌐 Full Schedule (lolworlds.com)", true, None::<&str>)?;
            let kofi_support = MenuItem::with_id(app, "kofi_support", "☕ Support on Ko-fi", true, None::<&str>)?;
            let sep4 = PredefinedMenuItem::separator(app)?;

            let quit_i = MenuItem::with_id(app, "quit", "Quit RiftWatch", true, None::<&str>)?;

            let menu = Menu::with_items(
                app,
                &[
                    &show_i,
                    &hide_i,
                    &sep1,
                    &nav_live,
                    &nav_schedule,
                    &nav_stream,
                    &nav_watchlist,
                    &nav_news,
                    &nav_settings,
                    &sep2,
                    &toggle_hud,
                    &sep3,
                    &stream_twitch,
                    &stream_youtube,
                    &stream_sched,
                    &kofi_support,
                    &sep4,
                    &quit_i,
                ],
            )?;

            let tray_icon = match tauri::image::Image::from_bytes(include_bytes!("../icons/32x32.png")) {
                Ok(img) => Some(img),
                Err(_) => app.default_window_icon().cloned(),
            };

            let mut builder = TrayIconBuilder::new()
                .menu(&menu)
                .tooltip("RiftWatch - LoL Esports Companion")
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "show" => {
                            if let Some(w) = app.get_webview_window("main") {
                                let _ = w.show();
                                let _ = w.unminimize();
                                let _ = w.set_focus();
                            }
                        }
                        "hide" => {
                            if let Some(w) = app.get_webview_window("main") {
                                let _ = w.hide();
                            }
                        }
                        "nav_live" | "nav_schedule" | "nav_stream" | "nav_watchlist" | "nav_news" | "nav_settings" => {
                            let tab = match event.id.as_ref() {
                                "nav_live" => "live",
                                "nav_schedule" => "schedule",
                                "nav_stream" => "stream",
                                "nav_watchlist" => "watchlist",
                                "nav_news" => "news",
                                "nav_settings" => "settings",
                                _ => "live",
                            };
                            if let Some(w) = app.get_webview_window("main") {
                                let _ = w.show();
                                let _ = w.unminimize();
                                let _ = w.set_focus();
                                let _ = w.emit("navigate_tab", tab);
                            }
                        }
                        "toggle_hud" => {
                            // Let the main window flip the setting so the toggle and Settings stay in sync.
                            if let Some(w) = app.get_webview_window("main") {
                                let _ = w.emit("toggle_hud", ());
                            } else if let Some(w) = app.get_webview_window("ticker") {
                                if w.is_visible().unwrap_or(false) {
                                    let _ = w.hide();
                                } else {
                                    let _ = w.show();
                                }
                            }
                        }
                        "stream_twitch" => {
                            open_url_checked(app, "https://www.twitch.tv/LoLWorldChampionship");
                        }
                        "stream_youtube" => {
                            open_url_checked(app, "https://www.youtube.com/@LoLWorldChampionships/live");
                        }
                        "stream_sched" => {
                            open_url_checked(app, "https://lolworlds.com");
                        }
                        "kofi_support" => {
                            open_url_checked(app, "https://ko-fi.com/monocle");
                        }
                        "quit" => {
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(w) = app.get_webview_window("main") {
                            if w.is_visible().unwrap_or(false) {
                                let _ = w.hide();
                            } else {
                                let _ = w.show();
                                let _ = w.unminimize();
                                let _ = w.set_focus();
                            }
                        }
                    }
                });

            if let Some(icon) = tray_icon {
                builder = builder.icon(icon);
            }

            let _ = builder.build(app)?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                if window.label() == "main" {
                    if CLOSE_TO_TRAY.load(Ordering::Relaxed) {
                        api.prevent_close();
                        let _ = window.hide();
                    } else {
                        window.app_handle().exit(0);
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
