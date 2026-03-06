/* ═══════════════════════════════════════════════════════
   THE CLOUD — booking mini-app — app.js
   ═══════════════════════════════════════════════════════ */

const tg = window.Telegram?.WebApp;
if (tg) { tg.expand(); tg.setHeaderColor("#080c14"); tg.setBackgroundColor("#080c14"); tg.disableVerticalSwipes?.(); }

/* ─────────── i18n ─────────── */
const STRINGS = {
  ru: {
    hints: ["Выбор стола", "Дата и время", "Детали брони", "Готово"],
    hint_default: "Бронирование столика",
    hh_hookah: "Кальян", hh_cocktails: "Коктейли + разливное пиво", hh_food: "Все блюда кухни",
    hall_main: "🏛 Основной зал", hall_second: "🔝 2 этаж",
    hall_label_main: "🏛 Основной зал", hall_label_second: "🔝 2 этаж",
    sec_hall: "Зал", sec_date: "Дата", sec_time: "Время", sec_guests: "Гостей", sec_data: "Данные",
    leg_free: "Свободен", leg_pend: "Ожидает", leg_enroute: "В пути", leg_busy: "Забронирован",
    live_busy: "Забронирован",
    staircase: "ЛЕСТНИЦА НА 2-Й ЭТАЖ",
    sel_badge_pre: "Стол", sel_badge_suf: "выбран",
    cap_one: "1 чел", cap_many: (n) => `${n} чел`,
    table_prefix: "Стол",
    lbl_free: "свободен", lbl_pend: "ожидает", lbl_busy: "забронирован",
    btn_to_datetime: "Выбрать дату и время →",
    btn_continue: "Продолжить →",
    btn_submit: "Подтвердить бронь",
    foot_note: "Администратор подтвердит в течение 15 мин",
    date_placeholder: "Выберите дату",
    time_placeholder: "Выберите дату…",
    months: ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"],
    ph_name: "Ваше имя", ph_phone: "+7 XXX XXX XXXX", ph_tg: "@username (необязательно)", ph_comment: "Пожелания, повод (необязательно)",
    cap_hint: (n) => `Макс. вместимость: ${n} чел.`,
    deposit_title: "Требуется депозит", deposit_none: "Не требуется",
    deposit_time: "С 18:00 – 00:00",
    dep_none: "Не требуется",
    toast_sel_table: "Выберите стол", toast_sel_date: "Выберите дату", toast_sel_time: "Выберите время",
    toast_enter_name: "Введите имя", toast_enter_phone: "Введите телефон",
    toast_enter_guests: "Укажите количество гостей",
    toast_cap_warn: (table, cap) => `Стол ${table} — макс. ${cap} чел. Пожалуйста выберите другой стол на предыдущем шаге.`,
    toast_cap_err: (table, cap) => `Стол ${table} вмещает макс. ${cap} чел. Выберите другой стол.`,
    toast_book_err: "Ошибка бронирования", toast_no_conn: "Нет соединения",
    done_title: "Бронь принята!", done_sub: "Мы свяжемся с вами для подтверждения",
    btn_my_bookings: "📋 Мои бронирования", btn_close: "Закрыть",
    lbl_hall: "Зал", lbl_table: "Стол", lbl_date: "Дата", lbl_time: "Время",
    lbl_guests: "Гостей", lbl_name: "Имя", lbl_phone: "Телефон", lbl_deposit: "Депозит",
    guest_vip: "VIP: ",
    guest_visits: (n) => n > 0 ? `${n} визит${n===1?"":(n<5?"а":"ов")} в ресторане` : "Новый гость",
    ts_confirm: "Выбрать этот стол", ts_cancel: "Отмена", ts_close: "Закрыть",
    ts_book: "📅 Забронировать этот стол",
    ts_cap_lbl: "👥 Вместимость", ts_dep_lbl: "💳 Депозит", ts_stat_lbl: "📍 Статус",
    ts_prefix: "Стол", ts_cap_until: (cap) => `до ${cap} чел.`,
    ts_warn_cap: (cap, sel) => `⚠️ Вместимость стола — ${cap} чел., выбрано ${sel}`,
    ts_warn_booked: "🕐 На сегодня уже есть бронь — выберите другое время",
    ts_live_pend: "🟡 Ожидает подтверждения", ts_live_free: "✅ Свободен", ts_live_confirmed: "🔴 Забронирован", ts_live_enroute: "🟠 В пути",
    ts_bookings_lbl: "📋 Брони на сегодня",
    ts_loading: "загрузка…", ts_no_bookings: "Броней нет", ts_load_err: "Ошибка загрузки",
    ts_cancel_booking: "Снять бронь? Гость получит уведомление об отмене.",
    ts_arrived_confirm: "Подтвердить что гость пришёл?",
    ts_booking_cancelled: "✅ Бронь отменена",
    ts_cancel_book_btn: "❌ Снять бронь", ts_move_btn: "↗️ Пересадить",
    mbs_title: "📋 Мои бронирования", mbs_loading: "Загрузка…",
    mbs_empty: "Бронирований нет", mbs_error: "Ошибка загрузки",
    status_pending: "Ожидает", status_confirmed: "Подтверждена", status_en_route: "В пути", status_cancelled: "Отменена",
    live_updated: (hh, mm) => `Обновлено: ${hh}:${mm}`,
    live_free: "Свободен", live_pend: "Ожидает", live_soon: "предстоит",
    live_slabel_free: "Свободен", live_slabel_pend: "Ожидает", live_slabel_enroute: "В пути", live_slabel_busy: "Забронирован",
    tab_booking: "Бронирование", tab_bookings: "Брони", tab_tables: "Столы", tab_guests: "Гости",
    filter_pending: "🔔 Ожидают", filter_confirmed: "✅ Подтв.", filter_en_route: "🟠 В пути",
    staff_title_pending: "🔔 Ожидают подтверждения",
    staff_title_confirmed: "✅ Подтверждённые сегодня",
    staff_title_en_route: "🟠 Гости в пути",
    staff_title_occupied: "🪑 Занятые столики",
    staff_loading: "Загрузка…", staff_forbidden: "⛔ Доступ запрещён", staff_error: "Ошибка загрузки",
    staff_count_pending_0: "Нет броней, ожидающих подтверждения",
    staff_count_pending_n: (n) => `${n} ожидают подтверждения`,
    staff_count_confirmed_0: "Нет подтверждённых броней сегодня",
    staff_count_confirmed_n: (n) => `${n} подтверждено сегодня`,
    staff_empty_pending: "✅ Все брони подтверждены",
    staff_empty_confirmed: "Нет подтверждённых броней сегодня",
    staff_empty_en_route: "Нет гостей в пути",
    staff_count_en_route_0: "Нет гостей в пути",
    staff_count_en_route_n: (n) => `${n} в пути`,
    loading: "Загрузка…", error_load: "Ошибка загрузки",
    no_slots: "Нет свободных слотов на эту дату", no_avail_slots: "Нет доступных слотов",
    walkin_title: (cell) => `🚶 Стол ${cell} — посадка по факту`,
    walkin_guests_lbl: "Кол-во гостей", walkin_name_lbl: "Имя (необязательно)",
    walkin_name_ph: "Гость без брони", walkin_comment_lbl: "Комментарий (необязательно)",
    walkin_comment_ph: "Например: день рождения", walkin_confirm: "✅ Посадить", walkin_cancel: "Отмена",
    walkin_ok: (cell, n) => `✅ Стол ${cell} занят · ${n} гостей`,
    walkin_sitbtn: "🚶 Посадить по факту",
    seat_enroute_btn: "🟠 Посадить гостя из «В пути»",
    seat_enroute_title: (cell) => `🟠 Посадить за стол ${cell}`,
    seat_enroute_empty: "Нет гостей в пути",
    seat_enroute_ok: (name, cell) => `✅ ${name} посажен за стол ${cell}`,
    seat_enroute_guests: (n) => `👥 ${n} чел.`,
    close_table_btn: "🔓 Закрыть стол — гости ушли",
    close_table_confirm: (cell) => `Закрыть стол ${cell}? Гости расчитались и ушли.`,
    close_table_ok: (cell) => `✅ Стол ${cell} освобождён`,
    move_title: "↗️ Пересадить гостя", move_cancel: "Отмена",
    move_other_floor: (label) => `🔝 ${label} — другой этаж`,
    move_no_tables: "Нет доступных столов",
    move_ok: (table, suffix) => `✅ Гость пересажен за стол ${table}${suffix}`,
    occ_all_free: "🎉 Все столики свободны", occ_count_0: "Все столики свободны",
    occ_count_n: (n) => `${n} ${n===1?"занят":"занято"}`,
    occ_status_pending: "🔔 Ожидает", occ_status_en_route: "🟠 В пути", occ_status_confirmed: "✅ Занят",
    reg_count: (n) => `${n} гостей`, reg_empty: "Гостей не найдено",
    reg_loading: "Загрузка…", reg_error: "Ошибка загрузки",
    reg_visits: (n) => `${n} визит${n===1?"":(n<5?"а":"ов")}`,
    reg_btn_book: "📅 Забронировать", reg_btn_vip_off: "❌ Снять VIP", reg_btn_vip_on: "⭐ VIP",
    reg_btn_note: "📝 Заметки", reg_toast_book: (name) => `📅 Бронь для ${name}`,
    reg_vip_on: "⭐ VIP присвоен", reg_vip_off: "❌ VIP снят",
    reg_search_ph: "Имя или телефон…",
    add_guest_title: "➕ Добавить гостя", add_guest_phone_ph: "Телефон", add_guest_name_ph: "Имя",
    add_guest_notes_ph: "Заметка (необязательно)", add_guest_vip_lbl: "⭐ Отметить как VIP",
    add_guest_save: "Сохранить", add_guest_cancel: "Отмена",
    add_guest_ok: (name) => `✅ Гость ${name} сохранён`, add_guest_err: "Ошибка сохранения",
    add_guest_no_phone: "Введите номер телефона", add_guest_no_name: "Введите имя",
    notes_title: "📝 Заметка о госте", notes_save: "Сохранить", notes_cancel: "Отмена",
    notes_ok: "📝 Заметка сохранена",
    err_conn: "Ошибка связи", err_generic: (d) => `Ошибка: ${d}`, no_conn: "Нет соединения",
    tbl_in_sheet: (cell) => `Стол ${cell}`,
    hall_label: { main: "🏛 Основной зал", second: "🔝 2 этаж" },
    action_confirm_ok: "✅ Бронь подтверждена", action_reject_ok: "❌ Бронь отклонена",
    table_busy_alert: "⛔ Стол занят / Table is taken",
    table_lbl: "Стол ",
    tables_title: "🗺️ Столы онлайн",
    tables_now: "Сейчас",
    reg_filter_all: "👥 Все",
    regulars_title: "⭐ Постоянники",
    reg_subtab_guests: "👥 Гости",
    reg_subtab_blacklist: "🚫 Чёрный список",
    bl_title: "🚫 Чёрный список",
    bl_empty: "Чёрный список пуст",
    bl_add_title: "➕ Добавить в чёрный список",
    bl_add_phone_ph: "Телефон (необязательно)",
    bl_add_tg_ph: "@username (необязательно)",
    bl_add_name_ph: "Имя гостя (необязательно)",
    bl_add_reason_ph: "Причина (необязательно)",
    bl_add_save: "Заблокировать",
    bl_add_cancel: "Отмена",
    bl_add_ok: (n) => `🚫 ${n || 'Гость'} добавлен в чёрный список`,
    bl_add_err: "Ошибка сохранения",
    bl_add_no_id: "Введите телефон или @username",
    bl_remove_confirm: "Удалить из чёрного списка?",
    bl_remove_ok: "✅ Убран из чёрного списка",
    bl_remove_err: "Ошибка удаления",
    bl_phone: "📞", bl_tg: "✈️", bl_reason: "Причина:",
    bl_date_lbl: "Добавлен:",
    bl_blocked_msg: (r) => r ? `⛔ Бронирование отклонено: ${r}` : "⛔ Вы в чёрном списке заведения",
    refresh: "Обновить",
    note_vip_sofa: "VIP диван",
    note_bar_seat: "Барное место",
    timeout_lbl: "⏰ Время истекло",
    guests_lbl: "Гостей:",
    guests_pax: (n) => `${n} чел.`,
    btn_confirm: "✅ Подтвердить",
    btn_reject: "❌ Отклонить",
    btn_arrived_yes: "✅ Да — гость пришёл",
    btn_arrived_no: "❌ Нет — не пришёл",
    remain_soon: "ещё",
    time_h: "ч", time_m: "м",
    bar_section: "🍺 Барная стойка",
    btn_menu_title: "Меню ресторана",
    btn_menu_sub: "Еда · Напитки · Кальян",
  },
  en: {
    hints: ["Select table", "Date & time", "Booking details", "Done"],
    hint_default: "Table Booking",
    hh_hookah: "Hookah", hh_cocktails: "Cocktails + draft beer", hh_food: "All food items",
    hall_main: "🏛 Main Hall", hall_second: "🔝 2nd Floor",
    hall_label_main: "🏛 Main Hall", hall_label_second: "🔝 2nd Floor",
    sec_hall: "Hall", sec_date: "Date", sec_time: "Time", sec_guests: "Guests", sec_data: "Details",
    leg_free: "Available", leg_pend: "Pending", leg_enroute: "On the way", leg_busy: "Booked",
    live_busy: "Booked",
    staircase: "STAIRS TO 2ND FLOOR",
    sel_badge_pre: "Table", sel_badge_suf: "selected",
    cap_one: "1 seat", cap_many: (n) => `${n} seats`,
    table_prefix: "Table",
    lbl_free: "available", lbl_pend: "pending", lbl_busy: "booked",
    btn_to_datetime: "Select date & time →",
    btn_continue: "Continue →",
    btn_submit: "Confirm booking",
    foot_note: "Admin will confirm within 15 min",
    date_placeholder: "Select date",
    time_placeholder: "Select date first…",
    months: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
    ph_name: "Your name", ph_phone: "+X XXX XXX XXXX", ph_tg: "@username (optional)", ph_comment: "Special requests, occasion (optional)",
    cap_hint: (n) => `Max capacity: ${n} seats`,
    deposit_title: "Deposit required", deposit_none: "No deposit",
    deposit_time: "From 18:00 – 00:00",
    dep_none: "No deposit",
    toast_sel_table: "Select a table", toast_sel_date: "Select a date", toast_sel_time: "Select a time",
    toast_enter_name: "Enter your name", toast_enter_phone: "Enter your phone",
    toast_enter_guests: "Select number of guests",
    toast_cap_warn: (table, cap) => `Table ${table} fits max ${cap} guests. Please choose another table.`,
    toast_cap_err: (table, cap) => `Table ${table} fits max ${cap} guests. Choose a different table.`,
    toast_book_err: "Booking error", toast_no_conn: "No connection",
    done_title: "Booking received!", done_sub: "We'll contact you shortly to confirm",
    btn_my_bookings: "📋 My bookings", btn_close: "Close",
    btn_menu_title: "Restaurant Menu",
    btn_menu_sub: "Food · Drinks · Hookah",
    lbl_hall: "Hall", lbl_table: "Table", lbl_date: "Date", lbl_time: "Time",
    lbl_guests: "Guests", lbl_name: "Name", lbl_phone: "Phone", lbl_deposit: "Deposit",
    guest_vip: "VIP: ",
    guest_visits: (n) => n > 0 ? `${n} visit${n===1?"":"s"} at the venue` : "New guest",
    ts_confirm: "Select this table", ts_cancel: "Cancel", ts_close: "Close",
    ts_book: "📅 Book this table",
    ts_cap_lbl: "👥 Capacity", ts_dep_lbl: "💳 Deposit", ts_stat_lbl: "📍 Status",
    ts_prefix: "Table", ts_cap_until: (cap) => `up to ${cap} seats`,
    ts_warn_cap: (cap, sel) => `⚠️ Table capacity is ${cap} seats, you selected ${sel}`,
    ts_warn_booked: "🕐 Already booked today — choose a different time",
    ts_live_pend: "🟡 Awaiting confirmation", ts_live_free: "✅ Available", ts_live_confirmed: "🔴 Booked", ts_live_enroute: "🟠 On the way",
    ts_bookings_lbl: "📋 Today's bookings",
    ts_loading: "loading…", ts_no_bookings: "No bookings", ts_load_err: "Load error",
    ts_cancel_booking: "Cancel booking? The guest will be notified.",
    ts_arrived_confirm: "Confirm that the guest has arrived?",
    ts_booking_cancelled: "✅ Booking cancelled",
    ts_cancel_book_btn: "❌ Cancel booking", ts_move_btn: "↗️ Move guest",
    mbs_title: "📋 My bookings", mbs_loading: "Loading…",
    mbs_empty: "No bookings", mbs_error: "Load error",
    status_pending: "Pending", status_confirmed: "Confirmed", status_en_route: "On the way", status_cancelled: "Cancelled",
    live_updated: (hh, mm) => `Updated: ${hh}:${mm}`,
    live_free: "Available", live_pend: "Pending", live_soon: "upcoming",
    live_slabel_free: "Available", live_slabel_pend: "Pending", live_slabel_enroute: "On the way", live_slabel_busy: "Booked",
    tab_booking: "Booking", tab_bookings: "Bookings", tab_tables: "Tables", tab_guests: "Guests",
    filter_pending: "🔔 Pending", filter_confirmed: "✅ Confirmed", filter_en_route: "🟠 On way",
    staff_title_pending: "🔔 Awaiting confirmation",
    staff_title_confirmed: "✅ Confirmed today",
    staff_title_en_route: "🟠 Guests on the way",
    staff_title_occupied: "🪑 Occupied tables",
    staff_loading: "Loading…", staff_forbidden: "⛔ Access denied", staff_error: "Load error",
    staff_count_pending_0: "No pending bookings",
    staff_count_pending_n: (n) => `${n} awaiting confirmation`,
    staff_count_confirmed_0: "No confirmed bookings today",
    staff_count_confirmed_n: (n) => `${n} confirmed today`,
    staff_empty_pending: "✅ All bookings confirmed",
    staff_empty_confirmed: "No confirmed bookings today",
    staff_empty_en_route: "No guests on the way",
    staff_count_en_route_0: "No guests on the way",
    staff_count_en_route_n: (n) => `${n} on the way`,
    loading: "Loading…", error_load: "Load error",
    no_slots: "No available slots for this date", no_avail_slots: "No available slots",
    walkin_title: (cell) => `🚶 Table ${cell} — walk-in`,
    walkin_guests_lbl: "Number of guests", walkin_name_lbl: "Name (optional)",
    walkin_name_ph: "Walk-in guest", walkin_comment_lbl: "Comment (optional)",
    walkin_comment_ph: "E.g.: birthday", walkin_confirm: "✅ Seat guests", walkin_cancel: "Cancel",
    walkin_ok: (cell, n) => `✅ Table ${cell} occupied · ${n} guests`,
    walkin_sitbtn: "🚶 Walk-in (seat now)",
    seat_enroute_btn: "🟠 Seat guest from «On the way»",
    seat_enroute_title: (cell) => `🟠 Seat at table ${cell}`,
    seat_enroute_empty: "No guests on the way",
    seat_enroute_ok: (name, cell) => `✅ ${name} seated at table ${cell}`,
    seat_enroute_guests: (n) => `👥 ${n} pax`,
    close_table_btn: "🔓 Free table — guests left",
    close_table_confirm: (cell) => `Free table ${cell}? Guests have settled and left.`,
    close_table_ok: (cell) => `✅ Table ${cell} freed`,
    move_title: "↗️ Move guest", move_cancel: "Cancel",
    move_other_floor: (label) => `🔝 ${label} — other floor`,
    move_no_tables: "No available tables",
    move_ok: (table, suffix) => `✅ Guest moved to table ${table}${suffix}`,
    occ_all_free: "🎉 All tables available", occ_count_0: "All tables available",
    occ_count_n: (n) => `${n} occupied`,
    occ_status_pending: "🔔 Pending", occ_status_en_route: "🟠 On the way", occ_status_confirmed: "✅ Occupied",
    reg_count: (n) => `${n} guests`, reg_empty: "No guests found",
    reg_loading: "Loading…", reg_error: "Load error",
    reg_visits: (n) => `${n} visit${n===1?"":"s"}`,
    reg_btn_book: "📅 Book", reg_btn_vip_off: "❌ Remove VIP", reg_btn_vip_on: "⭐ VIP",
    reg_btn_note: "📝 Notes", reg_toast_book: (name) => `📅 Booking for ${name}`,
    reg_vip_on: "⭐ VIP assigned", reg_vip_off: "❌ VIP removed",
    reg_search_ph: "Name or phone…",
    add_guest_title: "➕ Add guest", add_guest_phone_ph: "Phone", add_guest_name_ph: "Name",
    add_guest_notes_ph: "Note (optional)", add_guest_vip_lbl: "⭐ Mark as VIP",
    add_guest_save: "Save", add_guest_cancel: "Cancel",
    add_guest_ok: (name) => `✅ Guest ${name} saved`, add_guest_err: "Save error",
    add_guest_no_phone: "Enter phone number", add_guest_no_name: "Enter name",
    notes_title: "📝 Guest note", notes_save: "Save", notes_cancel: "Cancel",
    notes_ok: "📝 Note saved",
    err_conn: "Connection error", err_generic: (d) => `Error: ${d}`, no_conn: "No connection",
    tbl_in_sheet: (cell) => `Table ${cell}`,
    hall_label: { main: "🏛 Main Hall", second: "🔝 2nd Floor" },
    action_confirm_ok: "✅ Booking confirmed", action_reject_ok: "❌ Booking rejected",
    table_busy_alert: "⛔ Table is taken",
    table_lbl: "Table ",
    tables_title: "🗺️ Tables Live",
    tables_now: "Now",
    reg_filter_all: "👥 All",
    regulars_title: "⭐ Regulars",
    reg_subtab_guests: "👥 Guests",
    reg_subtab_blacklist: "🚫 Blacklist",
    bl_title: "🚫 Blacklist",
    bl_empty: "Blacklist is empty",
    bl_add_title: "➕ Add to blacklist",
    bl_add_phone_ph: "Phone (optional)",
    bl_add_tg_ph: "@username (optional)",
    bl_add_name_ph: "Guest name (optional)",
    bl_add_reason_ph: "Reason (optional)",
    bl_add_save: "Block",
    bl_add_cancel: "Cancel",
    bl_add_ok: (n) => `🚫 ${n || 'Guest'} added to blacklist`,
    bl_add_err: "Save error",
    bl_add_no_id: "Enter phone or @username",
    bl_remove_confirm: "Remove from blacklist?",
    bl_remove_ok: "✅ Removed from blacklist",
    bl_remove_err: "Remove error",
    bl_phone: "📞", bl_tg: "✈️", bl_reason: "Reason:",
    bl_date_lbl: "Added:",
    bl_blocked_msg: (r) => r ? `⛔ Booking rejected: ${r}` : "⛔ You are on the venue blacklist",
    refresh: "Refresh",
    note_vip_sofa: "VIP sofa",
    note_bar_seat: "Bar seat",
    timeout_lbl: "⏰ Time expired",
    guests_lbl: "Guests:",
    guests_pax: (n) => `${n} pax`,
    btn_confirm: "✅ Confirm",
    btn_reject: "❌ Decline",
    btn_arrived_yes: "✅ Yes — guest arrived",
    btn_arrived_no: "❌ No — no show",
    remain_soon: "soon",
    time_h: "h", time_m: "m",
    bar_section: "🍺 Bar Counter",
  },
  vi: {
    hints: ["Chọn bàn", "Ngày & giờ", "Chi tiết đặt chỗ", "Xong"],
    hint_default: "Đặt bàn",
    hh_hookah: "Thuốc lào", hh_cocktails: "Cocktail + bia tươi", hh_food: "Tất cả món ăn",
    hall_main: "🏛 Khu chính", hall_second: "🔝 Tầng 2",
    hall_label_main: "🏛 Khu chính", hall_label_second: "🔝 Tầng 2",
    sec_hall: "Khu", sec_date: "Ngày", sec_time: "Giờ", sec_guests: "Khách", sec_data: "Chi tiết",
    leg_free: "Trống", leg_pend: "Chờ xác nhận", leg_enroute: "Đang đến", leg_busy: "Đã đặt",
    live_busy: "Đã đặt",
    staircase: "CẦU THANG LÊN TẦNG 2",
    sel_badge_pre: "Bàn", sel_badge_suf: "đã chọn",
    cap_one: "1 người", cap_many: (n) => `${n} người`,
    table_prefix: "Bàn",
    lbl_free: "trống", lbl_pend: "chờ xác nhận", lbl_busy: "đã đặt",
    btn_to_datetime: "Chọn ngày & giờ →",
    btn_continue: "Tiếp tục →",
    btn_submit: "Xác nhận đặt chỗ",
    foot_note: "Quản trị viên sẽ xác nhận trong 15 phút",
    date_placeholder: "Chọn ngày",
    time_placeholder: "Chọn ngày trước…",
    months: ["Th1","Th2","Th3","Th4","Th5","Th6","Th7","Th8","Th9","Th10","Th11","Th12"],
    ph_name: "Tên của bạn", ph_phone: "+84 XXX XXX XXXX", ph_tg: "@username (không bắt buộc)", ph_comment: "Yêu cầu đặc biệt, dịp đặc biệt (không bắt buộc)",
    cap_hint: (n) => `Sức chứa tối đa: ${n} người`,
    deposit_title: "Yêu cầu đặt cọc", deposit_none: "Không cần đặt cọc",
    deposit_time: "Từ 18:00 – 00:00",
    dep_none: "Không cần đặt cọc",
    toast_sel_table: "Chọn bàn", toast_sel_date: "Chọn ngày", toast_sel_time: "Chọn giờ",
    toast_enter_name: "Nhập tên", toast_enter_phone: "Nhập số điện thoại",
    toast_enter_guests: "Chọn số lượng khách",
    toast_cap_warn: (table, cap) => `Bàn ${table} tối đa ${cap} người. Vui lòng chọn bàn khác.`,
    toast_cap_err: (table, cap) => `Bàn ${table} tối đa ${cap} người. Chọn bàn khác.`,
    toast_book_err: "Lỗi đặt chỗ", toast_no_conn: "Không có kết nối",
    done_title: "Đặt chỗ đã nhận!", done_sub: "Chúng tôi sẽ liên hệ để xác nhận",
    btn_my_bookings: "📋 Đặt chỗ của tôi", btn_close: "Đóng",
    btn_menu_title: "Thực đơn nhà hàng",
    btn_menu_sub: "Đồ ăn · Đồ uống · Thuốc lào",
    lbl_hall: "Khu", lbl_table: "Bàn", lbl_date: "Ngày", lbl_time: "Giờ",
    lbl_guests: "Khách", lbl_name: "Tên", lbl_phone: "Điện thoại", lbl_deposit: "Đặt cọc",
    guest_vip: "VIP: ",
    guest_visits: (n) => n > 0 ? `${n} lần ghé thăm` : "Khách mới",
    ts_confirm: "Chọn bàn này", ts_cancel: "Huỷ", ts_close: "Đóng",
    ts_book: "📅 Đặt bàn này",
    ts_cap_lbl: "👥 Sức chứa", ts_dep_lbl: "💳 Đặt cọc", ts_stat_lbl: "📍 Trạng thái",
    ts_prefix: "Bàn", ts_cap_until: (cap) => `tối đa ${cap} người`,
    ts_warn_cap: (cap, sel) => `⚠️ Bàn chứa tối đa ${cap} người, bạn chọn ${sel}`,
    ts_warn_booked: "🕐 Đã có đặt chỗ hôm nay — chọn giờ khác",
    ts_live_pend: "🟡 Chờ xác nhận", ts_live_free: "✅ Trống", ts_live_confirmed: "🔴 Đã đặt", ts_live_enroute: "🟠 Đang đến",
    ts_bookings_lbl: "📋 Đặt chỗ hôm nay",
    ts_loading: "đang tải…", ts_no_bookings: "Không có đặt chỗ", ts_load_err: "Lỗi tải",
    ts_cancel_booking: "Huỷ đặt chỗ? Khách sẽ nhận thông báo huỷ.",
    ts_arrived_confirm: "Xác nhận khách đã đến?",
    ts_booking_cancelled: "✅ Đã huỷ đặt chỗ",
    ts_cancel_book_btn: "❌ Huỷ đặt chỗ", ts_move_btn: "↗️ Đổi bàn",
    mbs_title: "📋 Đặt chỗ của tôi", mbs_loading: "Đang tải…",
    mbs_empty: "Không có đặt chỗ", mbs_error: "Lỗi tải",
    status_pending: "Chờ xác nhận", status_confirmed: "Đã xác nhận", status_en_route: "Đang đến", status_cancelled: "Đã huỷ",
    live_updated: (hh, mm) => `Cập nhật: ${hh}:${mm}`,
    live_free: "Trống", live_pend: "Chờ xác nhận", live_soon: "sắp tới",
    live_slabel_free: "Trống", live_slabel_pend: "Chờ xác nhận", live_slabel_enroute: "Đang đến", live_slabel_busy: "Đã đặt",
    tab_booking: "Đặt chỗ", tab_bookings: "Đặt chỗ", tab_tables: "Bàn", tab_guests: "Khách",
    filter_pending: "🔔 Chờ xác nhận", filter_confirmed: "✅ Đã xác nhận", filter_en_route: "🟠 Đang đến",
    staff_title_pending: "🔔 Chờ xác nhận",
    staff_title_confirmed: "✅ Đã xác nhận hôm nay",
    staff_title_en_route: "🟠 Khách đang đến",
    staff_title_occupied: "🪑 Bàn đang có khách",
    staff_loading: "Đang tải…", staff_forbidden: "⛔ Không có quyền truy cập", staff_error: "Lỗi tải",
    staff_count_pending_0: "Không có đặt chỗ chờ xác nhận",
    staff_count_pending_n: (n) => `${n} chờ xác nhận`,
    staff_count_confirmed_0: "Không có đặt chỗ đã xác nhận hôm nay",
    staff_count_confirmed_n: (n) => `${n} đã xác nhận hôm nay`,
    staff_empty_pending: "✅ Tất cả đặt chỗ đã xác nhận",
    staff_empty_confirmed: "Không có đặt chỗ đã xác nhận hôm nay",
    staff_empty_en_route: "Không có khách đang đến",
    staff_count_en_route_0: "Không có khách đang đến",
    staff_count_en_route_n: (n) => `${n} đang đến`,
    loading: "Đang tải…", error_load: "Lỗi tải",
    no_slots: "Không có chỗ trống cho ngày này", no_avail_slots: "Không có chỗ trống",
    walkin_title: (cell) => `🚶 Bàn ${cell} — khách vãng lai`,
    walkin_guests_lbl: "Số lượng khách", walkin_name_lbl: "Tên (không bắt buộc)",
    walkin_name_ph: "Khách vãng lai", walkin_comment_lbl: "Ghi chú (không bắt buộc)",
    walkin_comment_ph: "Ví dụ: sinh nhật", walkin_confirm: "✅ Đưa khách vào bàn", walkin_cancel: "Huỷ",
    walkin_ok: (cell, n) => `✅ Bàn ${cell} có khách · ${n} người`,
    walkin_sitbtn: "🚶 Đưa khách vào bàn",
    seat_enroute_btn: "🟠 Xếp chỗ khách đang đến",
    seat_enroute_title: (cell) => `🟠 Xếp vào bàn ${cell}`,
    seat_enroute_empty: "Không có khách đang đến",
    seat_enroute_ok: (name, cell) => `✅ ${name} đã vào bàn ${cell}`,
    seat_enroute_guests: (n) => `👥 ${n} người`,
    close_table_btn: "🔓 Giải phóng bàn — khách đã về",
    close_table_confirm: (cell) => `Giải phóng bàn ${cell}? Khách đã thanh toán và rời đi.`,
    close_table_ok: (cell) => `✅ Bàn ${cell} trống`,
    move_title: "↗️ Đổi bàn cho khách", move_cancel: "Huỷ",
    move_other_floor: (label) => `🔝 ${label} — tầng khác`,
    move_no_tables: "Không có bàn trống",
    move_ok: (table, suffix) => `✅ Khách đã chuyển sang bàn ${table}${suffix}`,
    occ_all_free: "🎉 Tất cả bàn đều trống", occ_count_0: "Tất cả bàn đều trống",
    occ_count_n: (n) => `${n} bàn có khách`,
    occ_status_pending: "🔔 Chờ xác nhận", occ_status_en_route: "🟠 Đang đến", occ_status_confirmed: "✅ Có khách",
    reg_count: (n) => `${n} khách`, reg_empty: "Không tìm thấy khách",
    reg_loading: "Đang tải…", reg_error: "Lỗi tải",
    reg_visits: (n) => `${n} lần ghé thăm`,
    reg_btn_book: "📅 Đặt chỗ", reg_btn_vip_off: "❌ Bỏ VIP", reg_btn_vip_on: "⭐ VIP",
    reg_btn_note: "📝 Ghi chú", reg_toast_book: (name) => `📅 Đặt chỗ cho ${name}`,
    reg_vip_on: "⭐ Đã cấp VIP", reg_vip_off: "❌ Đã bỏ VIP",
    reg_search_ph: "Tên hoặc số điện thoại…",
    add_guest_title: "➕ Thêm khách", add_guest_phone_ph: "Điện thoại", add_guest_name_ph: "Tên",
    add_guest_notes_ph: "Ghi chú (không bắt buộc)", add_guest_vip_lbl: "⭐ Đánh dấu VIP",
    add_guest_save: "Lưu", add_guest_cancel: "Huỷ",
    add_guest_ok: (name) => `✅ Khách ${name} đã lưu`, add_guest_err: "Lỗi lưu",
    add_guest_no_phone: "Nhập số điện thoại", add_guest_no_name: "Nhập tên",
    notes_title: "📝 Ghi chú về khách", notes_save: "Lưu", notes_cancel: "Huỷ",
    notes_ok: "📝 Đã lưu ghi chú",
    err_conn: "Lỗi kết nối", err_generic: (d) => `Lỗi: ${d}`, no_conn: "Không có kết nối",
    tbl_in_sheet: (cell) => `Bàn ${cell}`,
    hall_label: { main: "🏛 Khu chính", second: "🔝 Tầng 2" },
    action_confirm_ok: "✅ Đã xác nhận đặt chỗ", action_reject_ok: "❌ Đã từ chối đặt chỗ",
    table_busy_alert: "⛔ Bàn đã có khách",
    table_lbl: "Bàn ",
    tables_title: "🗺️ Bàn trực tuyến",
    tables_now: "Hiện tại",
    reg_filter_all: "👥 Tất cả",
    regulars_title: "⭐ Khách quen",
    reg_subtab_guests: "👥 Khách",
    reg_subtab_blacklist: "🚫 Danh sách đen",
    bl_title: "🚫 Danh sách đen",
    bl_empty: "Danh sách đen trống",
    bl_add_title: "➕ Thêm vào danh sách đen",
    bl_add_phone_ph: "Điện thoại (không bắt buộc)",
    bl_add_tg_ph: "@username (không bắt buộc)",
    bl_add_name_ph: "Tên khách (không bắt buộc)",
    bl_add_reason_ph: "Lý do (không bắt buộc)",
    bl_add_save: "Chặn",
    bl_add_cancel: "Huỷ",
    bl_add_ok: (n) => `🚫 ${n || 'Khách'} đã thêm vào danh sách đen`,
    bl_add_err: "Lỗi lưu",
    bl_add_no_id: "Nhập điện thoại hoặc @username",
    bl_remove_confirm: "Xoá khỏi danh sách đen?",
    bl_remove_ok: "✅ Đã xoá khỏi danh sách đen",
    bl_remove_err: "Lỗi xoá",
    bl_phone: "📞", bl_tg: "✈️", bl_reason: "Lý do:",
    bl_date_lbl: "Ngày thêm:",
    bl_blocked_msg: (r) => r ? `⛔ Đặt chỗ bị từ chối: ${r}` : "⛔ Bạn nằm trong danh sách đen",
    refresh: "Làm mới",
    note_vip_sofa: "Ghế sofa VIP",
    note_bar_seat: "Chỗ ngồi quầy bar",
    timeout_lbl: "⏰ Hết thời gian",
    guests_lbl: "Khách:",
    guests_pax: (n) => `${n} người`,
    btn_confirm: "✅ Xác nhận",
    btn_reject: "❌ Từ chối",
    btn_arrived_yes: "✅ Có — khách đã đến",
    btn_arrived_no: "❌ Không — khách không đến",
    remain_soon: "sắp",
    time_h: "g", time_m: "p",
    bar_section: "🍺 Quầy bar",
  },
};

let lang = (() => {
  const stored = localStorage.getItem("webapp_lang");
  if (stored) return stored;
  const tgLang = tg?.initDataUnsafe?.user?.language_code || "";
  if (tgLang.startsWith("ru")) return "ru";
  if (tgLang.startsWith("vi")) return "vi";
  return "en";
})();

function t(key, ...args) {
  const dict = STRINGS[lang] || STRINGS.ru;
  const val  = dict[key] !== undefined ? dict[key] : (STRINGS.ru[key] !== undefined ? STRINGS.ru[key] : key);
  return typeof val === "function" ? val(...args) : val;
}

function setLang(newLang) {
  lang = newLang;
  localStorage.setItem("webapp_lang", lang);
  // Update LAYOUTS hall labels for dynamic use
  LAYOUTS.main.hallLabel   = t("hall_main");
  LAYOUTS.second.hallLabel = t("hall_second");
  applyLang();
}

function applyLang() {
  // Toggle button label — shows current lang with flag
  const btn = document.getElementById("lang-toggle");
  if (btn) btn.textContent = lang === "ru" ? "🇷🇺 RU" : (lang === "vi" ? "🇻🇳 VI" : "🇬🇧 EN");

  // Update <html lang="..."> attribute
  document.documentElement.lang = lang;

  // Apply all data-i18n text content
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });

  // Apply placeholder translations
  document.querySelectorAll("[data-i18n-ph]").forEach(el => {
    el.placeholder = t(el.dataset.i18nPh);
  });

  // Apply title attribute translations
  document.querySelectorAll("[data-i18n-title]").forEach(el => {
    el.title = t(el.dataset.i18nTitle);
  });

  // Update LAYOUTS hall labels
  LAYOUTS.main.hallLabel   = t("hall_main");
  LAYOUTS.second.hallLabel = t("hall_second");

  // Update topbar hint
  const hintEl = document.getElementById("topbar-hint");
  const hints  = STRINGS[lang].hints;
  if (hintEl && hints) hintEl.textContent = hints[state.step] || hints[0];

  // Update date-display placeholder only when no date is selected
  const dd = document.getElementById("date-display");
  if (dd && !state.date) dd.textContent = t("date_placeholder");

  // Re-render custom calendar if open (language changed)
  if (typeof _calRender === "function" && _calEl && _calEl.style.display !== "none") _calRender();

  // Update time-grid placeholder only when empty
  const tg_el = document.getElementById("time-grid");
  if (tg_el && tg_el.querySelector(".muted-text") && !state.date) {
    tg_el.innerHTML = `<span class="muted-text">${t("time_placeholder")}</span>`;
  }

  // Update regulars search placeholder
  const rSearch = document.getElementById("regulars-search");
  if (rSearch) rSearch.placeholder = t("reg_search_ph");

  // Re-render floor plan to update embedded strings
  if (state.step === 0) renderFloorPlan();

  // ── Re-render dynamic sections currently on screen (language rehydration) ──
  if (staffView && staffView.style.display !== "none") {
    const titleEl = document.getElementById("staff-title");
    const countEl = document.getElementById("staff-count");
    if (titleEl) {
      if      (staffFilter === "pending")         titleEl.textContent = t("staff_title_pending");
      else if (staffFilter === "confirmed_today") titleEl.textContent = t("staff_title_confirmed");
      else if (staffFilter === "en_route")        titleEl.textContent = t("staff_title_en_route");
    }
    if (_staffBookingsCache !== null && _staffBookingsCache.filter === staffFilter) {
      const bk = _staffBookingsCache.bookings;
      if (countEl) {
        if (staffFilter === "pending") countEl.textContent = bk.length === 0 ? t("staff_count_pending_0") : t("staff_count_pending_n", bk.length);
        else if (staffFilter === "en_route") countEl.textContent = bk.length === 0 ? t("staff_count_en_route_0") : t("staff_count_en_route_n", bk.length);
        else                           countEl.textContent = bk.length === 0 ? t("staff_count_confirmed_0") : t("staff_count_confirmed_n", bk.length);
      }
      renderStaffList(bk);
    }
  }
  if (tablesView && tablesView.style.display !== "none" && _liveFloorCache !== null) {
    renderLiveFloor(_liveFloorCache.tables);
  }
  if (regularsView && regularsView.style.display !== "none") {
    _applyRegularsFilter();
  }
}

// Lang toggle button handler (attached after DOM ready — see bottom of file)

/* Pre-init screen 0 inline styles so no flash on load */
document.querySelectorAll(".screen").forEach((s, i) => {
  s.style.transition    = "none";
  s.style.transform     = i === 0 ? "translateX(0)" : "translateX(100%)";
  s.style.opacity       = i === 0 ? "1" : "0";
  s.style.pointerEvents = i === 0 ? "" : "none";
});

/* Fetch with timeout helper */
async function fetchT(url, opts, ms = 8000) {
  const ctrl = new AbortController();
  const id   = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, { signal: ctrl.signal, ...opts });
  } finally {
    clearTimeout(id);
  }
}

/* ─────────── FLOOR PLAN LAYOUTS ─────────── */
const LAYOUTS = {
  main: {
    mode: "map",
    img:  "/static/floor-main.svg?v=7",
    svgW: 400, svgH: 460,
    hallLabel: "Основной зал",
    kitchenSide: true,
    sectionLabels: [{ x: 88.75, y: 64, key: "bar_section", vertical: true }],
    // rows/cols kept for renderLiveFloor & buildButtons backward-compat
    cols: 4,
    rows: [
      ["T3",  "T2",  null,  null],
      ["B1",  null,  null,  null],
      ["B2",  null,  null,  null],
      ["B3",  null,  null,  null],
      ["B4",  null,  null,  null],
      ["B5",  null,  null,  null],
      ["B6",  null,  null,  null],
    ],
    tables: {
      // x/y = centre as % of container; w/h = size as % of container width
      "T3":  { x: 15.5, y: 17.5, w: 10,  h: 20,  shape: "rect"   },
      "T2":  { x: 70.0, y: 17.5, w: 36,  h: 14,  shape: "rect"   },
      "B1":  { x: 71.0, y: 38.0, shape: "circle" },
      "B2":  { x: 71.0, y: 48.5, shape: "circle" },
      "B3":  { x: 71.0, y: 59.0, shape: "circle" },
      "B4":  { x: 71.0, y: 69.5, shape: "circle" },
      "B5":  { x: 71.0, y: 80.0, shape: "circle" },
      "B6":  { x: 71.0, y: 90.5, shape: "circle" },
    },
  },
  second: {
    mode: "map",
    img:  "/static/floor-second.svg",
    svgW: 400, svgH: 480,
    hallLabel: "2nd Floor",
    kitchenSide: false,
    cols: 4,
    rows: [
      [{id:"8", span:2}, {id:"7", span:2}],
      ["__GAP__"],
      [{id:"9", span:2}, {id:"6", span:2}],
      ["__GAP__"],
      [{id:"10",span:2}, {id:"5", span:2}],
      ["__GAP__"],
      [{id:"11",span:1}, {id:"4", span:3}],
    ],
    tables: {
      "8":  { x: 29.5, y: 12.5, w: 30,  h: 12,  shape: "rect" },
      "7":  { x: 80.0, y: 12.5, w: 19,  h: 11,  shape: "rect" },
      "9":  { x: 24.0, y: 31.0, w: 19,  h: 11,  shape: "rect" },
      "6":  { x: 74.5, y: 31.0, w: 30,  h: 12,  shape: "rect" },
      "10": { x: 24.0, y: 49.5, w: 19,  h: 11,  shape: "rect" },
      "5":  { x: 80.5, y: 50.5, w: 12,  h: 20,  shape: "rect" },
      "11": { x: 24.0, y: 68.0, w: 19,  h: 11,  shape: "rect" },
      "4":  { x: 69.5, y: 71.5, w: 40,  h: 13,  shape: "rect" },
    },
  },
};

/* ─────────── TABLE INFO ─────────── */
// cap = max guests, deposit in VND (0 = no deposit)
const TABLE_INFO = {
  // ── Основной зал ──
  "T2":  { cap: 4, deposit: 1_500_000, icon: "🛋",  noteKey: "note_vip_sofa" },
  "T3":  { cap: 2, deposit: 0,         icon: "☕",  noteKey: "" },
  // Bar seats
  "B1":  { cap: 1, deposit: 0, icon: "🍺", noteKey: "note_bar_seat" },
  "B2":  { cap: 1, deposit: 0, icon: "🍺", noteKey: "note_bar_seat" },
  "B3":  { cap: 1, deposit: 0, icon: "🍺", noteKey: "note_bar_seat" },
  "B4":  { cap: 1, deposit: 0, icon: "🍺", noteKey: "note_bar_seat" },
  "B5":  { cap: 1, deposit: 0, icon: "🍺", noteKey: "note_bar_seat" },
  "B6":  { cap: 1, deposit: 0, icon: "🍺", noteKey: "note_bar_seat" },
  // ── 2nd Floor ──
  "4":   { cap: 6, deposit: 2_000_000, icon: "🛋",  note: "" },
  "5":   { cap: 4, deposit: 1_200_000, icon: "🎮",  note: "PlayStation" },
  "6":   { cap: 4, deposit: 1_500_000, icon: "🛋",  note: "" },
  "7":   { cap: 2, deposit: 0,         icon: "☕",  note: "" },
  "8":   { cap: 4, deposit: 1_500_000, icon: "🛋",  note: "" },
  "9":   { cap: 2, deposit: 0,         icon: "☕",  note: "" },
  "10":  { cap: 2, deposit: 0,         icon: "☕",  note: "" },
  "11":  { cap: 2, deposit: 0,         icon: "☕",  note: "" },
};

function fmtDeposit(amount) {
  if (!amount) return t("dep_none");
  return amount.toLocaleString("ru-RU") + " ₫";
}

/* ─────────── STATE ─────────── */
let state = {
  hall:     "main",
  date:     "",
  time:     "",
  table:    "",
  guests:   "",
  name:     "",
  phone:    "",
  comment:  "",
  step:     0,
  prefilledGuest: null,   // { name, phone } set when booking from Regulars tab
};

let bookedTables  = {};   // {tableName: "pending"|"confirmed"}
let takenSlots    = [];
let staffFilter   = "pending";
let refreshTimer  = null;
let staffTimer    = null;
let isStaff       = false;

/* ─────────── STAFF DETECTION ─────────── */
const ADMIN_ID  = 1650713364;

async function detectStaff() {
  const uid    = tg?.initDataUnsafe?.user?.id || 0;
  const initData = tg?.initData || "";

  // Fast local check: known admin ID
  if (uid === ADMIN_ID) {
    isStaff = true;
    document.getElementById("tab-bar").style.display = "flex";
    return;
  }

  // Ask server for authoritative role (checks DB + env whitelist)
  if (initData) {
    try {
      const r = await fetchT(`/api/me/role?init_data=${encodeURIComponent(initData)}`);
      const d = await r.json();
      isStaff = d.role === "staff" || d.role === "admin";
    } catch {
      isStaff = false;
    }
  }

  if (isStaff) {
    document.getElementById("tab-bar").style.display = "flex";
  }
}

/* ─────────── HELPERS ─────────── */
// Wire up lang toggle button after DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("lang-toggle")?.addEventListener("click", () => {
    setLang(lang === "ru" ? "en" : (lang === "en" ? "vi" : "ru"));
  });
});

function haptic(type, style) {
  try {
    if (type === "impact") tg?.HapticFeedback?.impactOccurred(style || "medium");
    if (type === "notify")  tg?.HapticFeedback?.notificationOccurred(style || "success");
    if (type === "sel")     tg?.HapticFeedback?.selectionChanged();
  } catch {}
}

function toast(msg, isErr = false) {
  const old = document.querySelector(".toast");
  if (old) old.remove();
  const el = document.createElement("div");
  el.className = "toast" + (isErr ? " err" : "");
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

function spinner(show) {
  let el = document.getElementById("__spinner");
  if (show) {
    if (!el) {
      el = document.createElement("div");
      el.id = "__spinner";
      el.className = "spinner-overlay";
      el.innerHTML = '<div class="spinner"></div>';
      document.body.appendChild(el);
    }
  } else {
    el?.remove();
  }
}

function fmtDate(iso) {
  if (!iso) return "";
  const parts  = iso.split("-");
  const months = t("months");
  return `${parseInt(parts[2])} ${months[parseInt(parts[1])-1]}`;
}

function hallLabel(h) {
  const labels = { main: t("hall_main"), second: t("hall_second") };
  return labels[h] || LAYOUTS[h]?.hallLabel || h;
}

/* ─────────── SCREENS ─────────── */
const SPRING = 'opacity .42s cubic-bezier(0.22,1,0.36,1), transform .42s cubic-bezier(0.22,1,0.36,1)';

function screenSet(el, tx, opacity, transition, pointerEvents) {
  el.style.transition    = transition    ?? '';
  el.style.transform     = tx            ?? '';
  el.style.opacity       = opacity != null ? String(opacity) : '';
  el.style.pointerEvents = pointerEvents ?? '';
}

function goTo(step) {
  const screens  = [...document.querySelectorAll(".screen")];
  const pips     = document.querySelectorAll(".pip");
  const back     = document.getElementById("global-back");
  const hint     = document.getElementById("topbar-hint");
  const goingBack = step < state.step;
  const prevStep  = state.step;

  if (step === prevStep) {
    // just refresh active screen state without animation
    pips.forEach((p,i) => p.classList.toggle("active", i <= step));
    back.style.display = step > 0 && step < 3 ? "flex" : "none";
    if (step === 0) { renderFloorPlan(); startRefresh(); }
    if (step === 2) fillFormMeta();
    return;
  }

  state.step = step;

  const incoming = screens[step];
  const leaving  = screens[prevStep];

  // ─ 1. Snap incoming to off-screen start (no transition) ─
  screenSet(incoming,
    goingBack ? 'translateX(-28%)' : 'translateX(100%)',
    goingBack ? 0.5 : 0,
    'none', 'none');
  incoming.classList.remove("active", "slide-out", "slide-back-out");

  void incoming.offsetHeight; // flush layout so start position commits

  // ─ 2. Animate leaving screen out ─
  screenSet(leaving,
    goingBack ? 'translateX(100%)' : 'translateX(-28%)',
    0.3, SPRING, 'none');
  leaving.classList.remove("active", "slide-out", "slide-back-out");

  // ─ 3. Animate incoming to centre (next paint frame) ─
  requestAnimationFrame(() => {
    screenSet(incoming, 'translateX(0)', 1, SPRING, '');
    incoming.classList.add("active");
  });

  // ─ 4. Hide all other screens instantly ─
  screens.forEach((s, i) => {
    if (i !== step && i !== prevStep) {
      screenSet(s, 'translateX(100%)', 0, 'none', 'none');
      s.classList.remove("active", "slide-out", "slide-back-out");
    }
  });

  // ─ 5. UI chrome ─
  pips.forEach((p,i) => p.classList.toggle("active", i <= step));
  back.style.display = step > 0 && step < 3 ? "flex" : "none";
  hint.textContent = (STRINGS[lang].hints || STRINGS.ru.hints)[step] || "";

  if (step === 0) { bookedTables = {}; renderFloorPlan(); loadFloorPlan(); startRefresh(); }
  else { stopRefresh(); }
  if (step === 1) {
    // Update meta-pill with selected hall and table
    const fHall = document.getElementById("f-hall");
    const fTable = document.getElementById("f-table");
    if (fHall) fHall.textContent = hallLabel(state.hall);
    if (fTable) fTable.textContent = state.table || "—";
    // Reset time selection when returning to this step
    state.time = "";
    document.querySelectorAll(".time-chip").forEach(c => c.classList.remove("sel"));
    const btnForm = document.getElementById("btn-to-form");
    if (btnForm) btnForm.disabled = true;
    if (state.date) loadSlots();
  }
  if (step === 2) fillFormMeta();
}

/* ─────────── SCREEN 0: DATE / TIME / HALL ─────────── */
const dateInput   = document.getElementById("date-input");
const dateDisplay = document.getElementById("date-display");
const timeGrid    = document.getElementById("time-grid");
const dateRow     = document.getElementById("date-row");

// Min date = today (Vietnam time, UTC+7)
function getVNDateISO() {
  try {
    return new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Ho_Chi_Minh" });
  } catch {
    const off = new Date(Date.now() + 7 * 3600_000);
    return off.toISOString().split("T")[0];
  }
}
const todayISO = getVNDateISO();
dateInput.setAttribute("min", todayISO);

/* ─── Desktop detection: use custom calendar when native picker fails ─── */
const _tgPlatform = (tg?.platform || "").toLowerCase();
const _isDesktop = ["tdesktop","macos","web","weba","webk","unigram","unknown"].includes(_tgPlatform)
                 || (!_tgPlatform && !/Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent));

// On desktop, disable the hidden native date input so it doesn't intercept clicks
if (_isDesktop) {
  dateInput.style.pointerEvents = "none";
  dateInput.tabIndex = -1;
}

/* ─── Custom calendar state ─── */
const _calEl      = document.getElementById("custom-cal");
const _calTitle   = document.getElementById("cal-title");
const _calDays    = document.getElementById("cal-days");
const _calPrev    = document.getElementById("cal-prev");
const _calNext    = document.getElementById("cal-next");
const _calReset   = document.getElementById("cal-reset");
const _calOk      = document.getElementById("cal-ok");
let _calYear, _calMonth, _calSelected = null; // _calSelected = "YYYY-MM-DD" or null

const _MONTHS_FULL = {
  ru: ["Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"],
  en: ["January","February","March","April","May","June","July","August","September","October","November","December"],
  vi: ["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6","Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"],
};
const _WDAYS = {
  ru: ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"],
  en: ["Mo","Tu","We","Th","Fr","Sa","Su"],
  vi: ["T2","T3","T4","T5","T6","T7","CN"],
};

function _calUpdateWeekdays() {
  const wd = document.querySelector(".custom-cal-weekdays");
  if (!wd) return;
  const days = _WDAYS[state.lang] || _WDAYS.ru;
  wd.innerHTML = days.map(d => `<span>${d}</span>`).join("");
}

function _calRender() {
  if (!_calEl) return;
  const mNames = _MONTHS_FULL[state.lang] || _MONTHS_FULL.ru;
  _calTitle.textContent = `${mNames[_calMonth]} ${_calYear} г.`;
  _calUpdateWeekdays();

  // Min date parts
  const [minY, minM, minD] = todayISO.split("-").map(Number);
  // Disable prev if we're at the min month
  _calPrev.disabled = (_calYear === minY && _calMonth === minM - 1);

  // First day of month (0=Sun..6=Sat) → shift to Mon=0
  const firstDay = new Date(_calYear, _calMonth, 1).getDay();
  const offset = (firstDay + 6) % 7; // Mon-based offset
  const daysInMonth = new Date(_calYear, _calMonth + 1, 0).getDate();

  let html = "";
  // Empty cells before first day
  for (let i = 0; i < offset; i++) html += `<span class="cd-cell cd-empty"></span>`;

  for (let d = 1; d <= daysInMonth; d++) {
    const iso = `${_calYear}-${String(_calMonth+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
    const isPast = (_calYear < minY) || (_calYear === minY && _calMonth < minM - 1)
                 || (_calYear === minY && _calMonth === minM - 1 && d < minD);
    const isToday = (iso === todayISO);
    const isSel   = (iso === _calSelected);
    let cls = "cd-cell";
    if (isPast)   cls += " cd-disabled";
    if (isToday && !isSel) cls += " cd-today";
    if (isSel)    cls += " cd-selected";
    html += `<span class="${cls}" data-date="${iso}">${d}</span>`;
  }
  _calDays.innerHTML = html;
  _calOk.disabled = !_calSelected;
}

function _calOpen() {
  if (!_calEl) return;
  const [y, m] = (state.date || todayISO).split("-").map(Number);
  _calYear = y;
  _calMonth = m - 1;
  _calSelected = state.date || null;
  _calRender();
  _calEl.style.display = "";
}

function _calClose() {
  if (_calEl) _calEl.style.display = "none";
}

function _calApply(iso) {
  state.date = iso;
  dateInput.value = iso;
  state.time = "";
  const btnForm = document.getElementById("btn-to-form");
  if (btnForm) btnForm.disabled = true;
  dateDisplay.textContent = fmtDate(iso);
  _calClose();
  loadSlots();
  haptic("sel");
}

if (_calEl) {
  _calDays.addEventListener("click", e => {
    const cell = e.target.closest(".cd-cell");
    if (!cell || cell.classList.contains("cd-disabled") || cell.classList.contains("cd-empty")) return;
    _calSelected = cell.dataset.date;
    _calRender();
    haptic("sel");
  });
  _calPrev.addEventListener("click", () => {
    _calMonth--;
    if (_calMonth < 0) { _calMonth = 11; _calYear--; }
    _calRender();
  });
  _calNext.addEventListener("click", () => {
    _calMonth++;
    if (_calMonth > 11) { _calMonth = 0; _calYear++; }
    _calRender();
  });
  _calReset.addEventListener("click", () => {
    _calSelected = null;
    _calRender();
  });
  _calOk.addEventListener("click", () => {
    if (_calSelected) _calApply(_calSelected);
  });
}

dateRow.addEventListener("click", () => {
  if (_isDesktop && _calEl) {
    // Toggle custom calendar on desktop
    if (_calEl.style.display === "none" || !_calEl.style.display) _calOpen();
    else _calClose();
    return;
  }
  // Mobile: use native picker
  try { dateInput.showPicker(); } catch { dateInput.click(); }
});
dateInput.addEventListener("change", () => {
  state.date = dateInput.value;
  state.time = "";
  const btnForm = document.getElementById("btn-to-form");
  if (btnForm) btnForm.disabled = true;
  dateDisplay.textContent = fmtDate(state.date);
  _calClose();
  loadSlots();
  haptic("sel");
});

// Hall tabs
document.getElementById("hall-tabs").addEventListener("click", e => {
  const btn = e.target.closest(".seg-btn");
  if (!btn) return;
  state.hall = btn.dataset.hall;
  state.table = "";
  document.querySelectorAll("#hall-tabs .seg-btn").forEach(b => b.classList.toggle("active", b === btn));
  haptic("sel");
  // Re-render floor plan with new hall
  bookedTables = {};
  renderFloorPlan();
  loadFloorPlan();
});

async function loadSlots() {
  timeGrid.innerHTML = `<span class="muted-text">${t("loading")}</span>`;
  try {
    // Filter slots by specific table when table is selected
    const url = state.table
      ? `/api/slots/table?hall=${state.hall}&table=${encodeURIComponent(state.table)}&date=${state.date}`
      : `/api/slots?hall=${state.hall}&date=${state.date}`;
    const r = await fetchT(url);
    const d = await r.json();
    const rawSlots = d.slots || [];
    const allTimes = rawSlots.filter(s => s.available !== false).map(s => s.time || s);
    takenSlots = rawSlots.filter(s => s.available === false).map(s => s.time || s);
    if (allTimes.length === 0) {
      timeGrid.innerHTML = `<span class="muted-text">${t("no_slots")}</span>`;
    } else {
      renderTimeGrid(allTimes);
    }
  } catch {
    timeGrid.innerHTML = `<span class="muted-text">${t("error_load")}</span>`;
  }
}

// Convert slot "HH:MM" to comparable minutes (00:xx-02:xx treated as 24:xx-26:xx)
function slotToMinutes(t) {
  const [h, m] = t.split(":").map(Number);
  const adj = h <= 2 ? h + 24 : h;  // midnight slots: 00→24, 01→25, 02→26
  return adj * 60 + m;
}

function isPastSlot(t) {
  // Only disable past slots when booking for today (VN date)
  if (state.date !== getVNDateISO()) return false;
  try {
    const now    = new Date();
    const vnStr  = now.toLocaleTimeString("en-GB", { timeZone: "Asia/Ho_Chi_Minh",
                     hour: "2-digit", minute: "2-digit" });
    const [ch, cm] = vnStr.split(":").map(Number);
    const nowMins  = (ch <= 2 ? ch + 24 : ch) * 60 + cm;
    return slotToMinutes(t) <= nowMins;  // current slot already started or passed
  } catch { return false; }
}

function renderTimeGrid(slots) {
  if (!slots.length) { timeGrid.innerHTML = `<span class="muted-text">${t("no_avail_slots")}</span>`; return; }
  timeGrid.innerHTML = "";
  slots.forEach(t => {
    const past = isPastSlot(t);
    const btn  = document.createElement("button");
    btn.className = "time-chip" + (past ? " past" : "");
    btn.textContent = t;
    btn.disabled = past;
    if (!past) {
      btn.addEventListener("click", () => {
        if (state.time === t) return;
        state.time = t;
        document.querySelectorAll(".time-chip").forEach(c => c.classList.toggle("sel", c.textContent === t));
        const btnForm = document.getElementById("btn-to-form");
        if (btnForm) btnForm.disabled = false;
        haptic("sel");
      });
    }
    timeGrid.appendChild(btn);
    if (state.time === t) btn.classList.add("sel");
  });
}

document.getElementById("btn-to-datetime").addEventListener("click", () => {
  if (!state.table) { toast(t("toast_sel_table"), true); return; }
  haptic("impact");
  goTo(1);
});

/* ─────────── SCREEN 0: FLOOR PLAN ─────────── */
async function loadFloorPlan() {
  try {
    // Use live endpoint so pending (purple) bookings anywhere in the day are shown
    const date = getVNDateISO();
    const now  = new Date();
    const vnStr = now.toLocaleTimeString("en-GB", { timeZone: "Asia/Ho_Chi_Minh", hour: "2-digit", minute: "2-digit" });
    const [hh, mm] = vnStr.split(":").map(Number);
    const cur_min = (hh <= 2 ? hh + 24 : hh) * 60 + mm;
    const r = await fetchT(`/api/tables/live?hall=${state.hall}&date=${date}&current_minutes=${cur_min}`);
    const d = await r.json();
    // Convert live format {T1:{status,remaining_min}} → simple {T1:"pending"} map
    const liveData = d.tables || {};
    bookedTables = {};
    Object.entries(liveData).forEach(([k, v]) => {
      if (v && v.status && v.status !== "free") bookedTables[k] = v.status;
    });
    renderFloorPlan();
  } catch {
    console.warn("floor plan load error");
  }
}

function renderFloorPlan() {
  const layout = LAYOUTS[state.hall];
  const fp     = document.getElementById("floor-plan");
  const meta   = document.getElementById("floor-label-bot");
  if (meta) meta.style.display = layout.kitchenSide ? "" : "none";

  fp.className = "floor-map";
  fp.removeAttribute("style");
  fp.innerHTML = "";

  // Background SVG image
  const bg = document.createElement("img");
  bg.src       = layout.img + "?v=8";
  bg.alt       = layout.hallLabel;
  bg.draggable = false;
  bg.className = "floor-map-bg";
  fp.appendChild(bg);

  // Section labels (bar, staircase area, etc.)
  if (layout.sectionLabels) {
    layout.sectionLabels.forEach(sec => {
      const lbl = document.createElement("div");
      lbl.className = "floor-section-lbl" + (sec.vertical ? " floor-section-lbl--vertical" : "");
      lbl.style.left = sec.x + "%";
      lbl.style.top  = sec.y + "%";
      lbl.textContent = t(sec.key);
      fp.appendChild(lbl);
    });
  }

  // Absolutely-positioned table pins
  Object.entries(layout.tables).forEach(([cellId, pos]) => {
    const rawStatus = bookedTables[cellId] || "free";
    const STATUS_CLASS = { free: "free", pending: "pending", en_route: "en_route", confirmed: "busy" };
    const status   = STATUS_CLASS[rawStatus] || "free";
    const isBooked = rawStatus !== "free";
    const isSelected = state.table === cellId;
    const info = TABLE_INFO[cellId];

    const el = document.createElement("div");
    el.className = `tbl tbl-pin ${isSelected ? "selected" : status}`;
    if (pos.shape === "circle") el.classList.add("tbl-pin-circle");
    if (info?.deposit > 0) el.classList.add("tbl-has-dep");

    el.style.left = pos.x + "%";
    el.style.top  = pos.y + "%";
    if (pos.shape === "circle") {
      el.style.width       = "12%";
      el.style.aspectRatio = "1";
    } else {
      if (pos.w) el.style.width  = pos.w + "%";
      if (pos.h) el.style.height = pos.h + "%";
    }

    const numSpan = document.createElement("span");
    numSpan.className   = "tbl-num";
    numSpan.textContent = cellId;
    el.appendChild(numSpan);

    if (pos.shape === "circle") {
      const stSpan = document.createElement("span");
      stSpan.className = "tbl-status";
      const STATUS_ICON = { free: "✓", pending: "●", busy: "✕" };
      stSpan.textContent = STATUS_ICON[status] || "✓";
      el.appendChild(stSpan);
    }

    if (info && pos.shape !== "circle") {
      const capSpan = document.createElement("span");
      capSpan.className   = "tbl-cap";
      capSpan.textContent = info.cap === 1 ? t("cap_one") : t("cap_many", info.cap);
      el.appendChild(capSpan);

      const stSpan = document.createElement("span");
      stSpan.className = "tbl-status";
      const STATUS_LBL = { free: t("lbl_free"), pending: t("lbl_pend"), busy: t("lbl_busy") };
      stSpan.textContent = STATUS_LBL[status] || t("lbl_free");
      el.appendChild(stSpan);
    }

    if (info?.deposit > 0) {
      const dot = document.createElement("span");
      dot.className = "tbl-dep-dot";
      dot.title     = t("deposit_title");
      el.appendChild(dot);
    }

    const LABEL = { free: t("lbl_free"), pending: t("lbl_pend"), busy: t("lbl_busy") };
    el.title = `${t("table_prefix")} ${cellId} — ${LABEL[status] || status}`;
    el.addEventListener("click", () => {
      haptic("impact", "light");
      showTableSheet(cellId, null, 0, isBooked);
    });
    fp.appendChild(el);
  });

  updateSelBadge();
  document.getElementById("btn-to-form").disabled = !state.table;
}

function updateSelBadge() {
  const badge = document.getElementById("sel-badge");
  const sName = document.getElementById("sel-name");
  if (state.table) {
    badge.style.display = "inline-flex";
    sName.textContent = state.table;
  } else {
    badge.style.display = "none";
  }
  const btnDatetime = document.getElementById("btn-to-datetime");
  if (btnDatetime) btnDatetime.disabled = !state.table;
}

/* ─────────── TABLE INFO SHEET ─────────── */
let _sheetPending  = "";
let _sheetLiveMode = false;  // true when sheet opened from live tables tab
let _sheetCell     = "";     // cell id currently shown in the sheet

// Confirm dialog that works inside Telegram WebApp
function tgConfirm(msg) {
  return new Promise(res => {
    if (tg?.showConfirm) {
      tg.showConfirm(msg, ok => res(!!ok));
    } else {
      res(window.confirm(msg));
    }
  });
}

// liveStatus: null = booking mode, "free"/"pending"/"confirmed" = live view mode
function showTableSheet(cell, liveStatus = null, remainMin = 0, hasBookingsToday = false) {
  _sheetCell = cell;
  const info   = TABLE_INFO[cell] || { cap: 4, deposit: 0, icon: "🪑", note: "" };
  const sheet  = document.getElementById("table-sheet");

  document.getElementById("ts-icon").textContent  = info.icon;
  document.getElementById("ts-title").textContent = t("tbl_in_sheet", cell);
  document.getElementById("ts-note").textContent  = info.noteKey ? t(info.noteKey) : (info.note || "");
  document.getElementById("ts-cap").textContent   = t("ts_cap_until", info.cap);

  const depEl = document.getElementById("ts-deposit");
  const depTimeEl = document.getElementById("ts-dep-time");
  if (info.deposit > 0) {
    depEl.textContent = info.deposit.toLocaleString("ru-RU") + " ₫";
    depEl.style.color = "var(--c-amber)";
    if (depTimeEl) { depTimeEl.style.display = ""; depTimeEl.textContent = t("deposit_time"); }
  } else {
    depEl.textContent = t("dep_none");
    depEl.style.color = "var(--c-green)";
    if (depTimeEl) depTimeEl.style.display = "none";
  }

  // Status row (live view only)
  let statusRow = document.getElementById("ts-status-row");
  if (!statusRow) {
    const rows = document.querySelector(".ts-rows");
    statusRow = document.createElement("div");
    statusRow.className = "ts-row";
    statusRow.id = "ts-status-row";
    statusRow.innerHTML = `<span class="ts-row-label">${t("ts_stat_lbl")}</span><span class="ts-row-val" id="ts-status-val">—</span>`;
    rows.insertBefore(statusRow, rows.firstChild);
  }
  const statusVal = document.getElementById("ts-status-val");
  if (liveStatus !== null) {
    const SLABEL = { free: t("ts_live_free"), pending: t("ts_live_pend"), en_route: t("ts_live_enroute"), confirmed: t("ts_live_confirmed") };
    const SCOLOR = { free: "var(--c-green)", pending: "#c084fc", en_route: "#f97316", confirmed: "#e05b5b" };
    const label  = SLABEL[liveStatus] || liveStatus;
    const remain = (liveStatus !== "free" && remainMin > 0)
      ? ` · ${t("remain_soon")} ${remainMin >= 60 ? Math.floor(remainMin/60)+t("time_h")+" "+(remainMin%60?remainMin%60+t("time_m"):"") : remainMin+t("time_m")}`
      : "";
    statusVal.textContent  = label + remain;
    statusVal.style.color  = SCOLOR[liveStatus] || "";
    statusRow.style.display = "";
  } else {
    statusRow.style.display = "none";
  }

  // Guests warning (booking mode only)
  const warn = document.getElementById("ts-warn");
  if (warn) {
    if (liveStatus === null) {
      const gNum = parseInt(state.guests) || (state.guests === "6+" ? 6 : 0);
      if (gNum > 0 && gNum > info.cap) {
        warn.style.display = "";
        warn.style.color = "var(--c-amber)";
        warn.textContent = t("ts_warn_cap", info.cap, state.guests);
      } else if (hasBookingsToday) {
        warn.style.display = "";
        warn.style.color = "#c084fc";
        warn.textContent = t("ts_warn_booked");
      } else {
        warn.style.display = "none";
      }
    } else {
      warn.style.display = "none";
    }
  }

  // Confirm / cancel buttons
  const confirmBtn = document.getElementById("ts-confirm");
  const cancelBtn  = document.getElementById("ts-cancel");
  if (liveStatus === null) {
    // Booking mode — original behaviour
    confirmBtn.style.display = "";
    confirmBtn.textContent   = t("ts_confirm");
    cancelBtn.textContent    = t("ts_cancel");
    _sheetPending = cell;
    _sheetLiveMode = false;
    document.getElementById("ts-walkin-btn")?.remove();
  } else if (liveStatus === "free") {
    // Live mode, free table — offer to book
    confirmBtn.style.display = "";
    confirmBtn.textContent   = t("ts_book");
    cancelBtn.textContent    = t("ts_close");
    _sheetPending  = cell;
    _sheetLiveMode = true;
    // Staff extra: walk-in button
    _ensureWalkInBtn(cell, liveStatus);
  } else {
    // Live mode, occupied table — info only
    confirmBtn.style.display = "none";
    cancelBtn.textContent    = t("ts_close");
    _sheetPending  = cell;
    _sheetLiveMode = false;
    _ensureWalkInBtn(cell, liveStatus);
  }

  // ── Live bookings list ──
  const bookSection = document.getElementById("ts-bookings-section");
  const bookList    = document.getElementById("ts-bookings-list");
  if (liveStatus !== null && bookSection && bookList) {
    const bookings_lbl = `<div style="font-size:12px;font-weight:600;color:var(--c-muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">${t("ts_bookings_lbl")}</div>`;
    bookSection.style.display = "";
    _loadTableBookings(cell, bookList);
  } else if (bookSection) {
    bookSection.style.display = "none";
  }

  sheet.style.display = "flex";
  requestAnimationFrame(() => sheet.classList.add("open"));
}

function _loadTableBookings(cell, listEl) {
  const resolvedCell = cell || _sheetCell;
  if (!resolvedCell) return;
  const bookList = listEl || document.getElementById("ts-bookings-list");
  if (!bookList) return;
  bookList.innerHTML = `<div style="color:var(--c-muted);font-size:13px;text-align:center;padding:6px 0">${t("ts_loading")}</div>`;
  const date = getVNDateISO();
  // Use liveHall when in tables tab, fall back to state.hall for booking tab
  const reqHall = (tablesView && tablesView.style.display !== "none") ? liveHall : state.hall;
  fetchT(`/api/table/bookings?hall=${encodeURIComponent(reqHall)}&table=${encodeURIComponent(resolvedCell)}&date=${encodeURIComponent(date)}`)
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(d => {
      const bks = d.bookings || [];
      if (bks.length === 0) {
        bookList.innerHTML = `<div style="color:var(--c-muted);font-size:13px;text-align:center;padding:6px 0">${t("ts_no_bookings")}</div>`;
        return;
      }
      bookList.innerHTML = "";
      bks.forEach(b => {
        const STATUS_COLOR = { confirmed: "#e05b5b", pending: "#c084fc", en_route: "#fb923c" };
        const card = document.createElement("div");
        card.style.cssText = `background:rgba(255,255,255,.07);border-radius:10px;padding:10px 12px;
          display:flex;flex-direction:column;gap:4px;
          border-left:3px solid ${STATUS_COLOR[b.status] || "#888"}`;

        const tgHandle = b.tg_username ? b.tg_username.replace(/^@/, '') : '';
        const tgUserId = b.tg_user_id || 0;
        let tgBtnHtml = '';
        if (isStaff) {
          if (tgHandle) {
            tgBtnHtml = `<a href="https://t.me/${tgHandle}" target="_blank" style="display:flex;align-items:center;justify-content:center;gap:5px;padding:5px 8px;border-radius:7px;background:rgba(41,182,246,.18);color:#7dd3f8;font-size:12px;text-decoration:none;flex:1">✈️ @${tgHandle}</a>`;
          } else if (tgUserId) {
            tgBtnHtml = `<a href="tg://user?id=${tgUserId}" style="display:flex;align-items:center;justify-content:center;gap:5px;padding:5px 8px;border-radius:7px;background:rgba(41,182,246,.18);color:#7dd3f8;font-size:12px;text-decoration:none;flex:1">✈️ Написать в Telegram</a>`;
          }
        }

        // Arrived button for en_route bookings — separate row, prominent orange
        const arrivedBtnHtml = (isStaff && b.status === "en_route") ? `
          <div style="margin-top:6px">
            <button onclick="arrivedBookingInSheet(${b.id},'${resolvedCell}')" style="width:100%;padding:8px 6px;border-radius:8px;border:none;background:rgba(249,115,22,.35);color:#fb923c;font-size:13px;font-weight:700;cursor:pointer">🟠 Пришли</button>
          </div>` : "";

        const actionsHtml = isStaff ? `
          <div style="display:flex;gap:6px;margin-top:6px">
            <button onclick="cancelBookingInSheet(${b.id},'${resolvedCell}')" style="flex:1;padding:5px 6px;border-radius:7px;border:none;background:rgba(220,50,50,.25);color:#ff8a8a;font-size:12px;cursor:pointer">${t("ts_cancel_book_btn")}</button>
            <button onclick="showMovePicker(${b.id},'${resolvedCell}')" style="flex:1;padding:5px 6px;border-radius:7px;border:none;background:rgba(80,150,255,.2);color:#7bb8ff;font-size:12px;cursor:pointer">${t("ts_move_btn")}</button>
          </div>
          ${arrivedBtnHtml}
          ${tgBtnHtml ? `<div style="display:flex;gap:6px;margin-top:4px">${tgBtnHtml}</div>` : ''}` : "";

        card.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-weight:600;font-size:14px">⏰ ${b.time}</span>
            <span style="font-size:11px;color:${STATUS_COLOR[b.status] || '#888'}">${t("status_" + b.status) || b.status}</span>
          </div>
          <div style="font-size:13px">👤 ${b.name} · 👥 ${t("guests_pax", b.guests_count)}</div>
          ${b.phone ? `<div style="font-size:12px;color:var(--c-muted);margin-top:1px">📞 ${b.phone}</div>` : ""}
          ${b.comment ? `<div style="font-size:12px;color:var(--c-muted);margin-top:2px">💬 ${b.comment}</div>` : ""}
          ${actionsHtml}
        `;
        bookList.appendChild(card);
      });
    })
    .catch(() => {
      bookList.innerHTML = `<div style="color:var(--c-muted);font-size:13px;text-align:center;padding:6px 0">${t("ts_load_err")}</div>`;
    });
}

function _ensureWalkInBtn(cell, liveStatus) {
  // Remove existing extra buttons
  document.getElementById("ts-walkin-btn")?.remove();
  document.getElementById("ts-seat-enroute-btn")?.remove();
  document.getElementById("ts-close-table-btn")?.remove();
  if (!isStaff) return;

  const cancelBtn = document.getElementById("ts-cancel");

  if (liveStatus === "free") {
    // Wrap both action buttons in a flex column container
    const wrapper = document.createElement("div");
    wrapper.id = "ts-seat-enroute-btn"; // use as anchor id for cleanup
    wrapper.style.cssText = `display:flex;flex-direction:column;gap:8px;margin-bottom:8px`;

    // Orange: seat en_route guest
    const seatBtn = document.createElement("button");
    seatBtn.textContent = t("seat_enroute_btn");
    seatBtn.style.cssText = `width:100%;padding:12px;border-radius:12px;border:none;
      background:rgba(249,115,22,.2);color:#fb923c;font-size:15px;font-weight:600;cursor:pointer;
      touch-action:manipulation`;
    seatBtn.onclick = () => showSeatEnRouteModal(cell);

    // Green: walk-in / seat by fact
    const walkBtn = document.createElement("button");
    walkBtn.id = "ts-walkin-btn";
    walkBtn.textContent = t("walkin_sitbtn");
    walkBtn.style.cssText = `width:100%;padding:12px;border-radius:12px;border:none;
      background:rgba(34,197,94,.2);color:#4ade80;font-size:15px;font-weight:600;cursor:pointer;
      touch-action:manipulation`;
    walkBtn.onclick = () => showWalkInModal(cell);

    wrapper.appendChild(seatBtn);
    wrapper.appendChild(walkBtn);
    cancelBtn.parentNode.insertBefore(wrapper, cancelBtn);
  } else if (liveStatus === "en_route") {
    // Walk-in (seat by fact) for en_route (orange) tables
    const btn = document.createElement("button");
    btn.id = "ts-walkin-btn";
    btn.textContent = t("walkin_sitbtn");
    btn.style.cssText = `width:100%;padding:12px;border-radius:12px;border:none;margin-bottom:8px;
      background:rgba(34,197,94,.18);color:#4ade80;font-size:15px;font-weight:600;cursor:pointer;
      touch-action:manipulation`;
    btn.onclick = () => showWalkInModal(cell);
    cancelBtn.parentNode.insertBefore(btn, cancelBtn);

    // Close table for en_route tables
    const closeBtn = document.createElement("button");
    closeBtn.id = "ts-close-table-btn";
    closeBtn.textContent = t("close_table_btn");
    closeBtn.style.cssText = `width:100%;padding:12px;border-radius:12px;border:none;margin-bottom:8px;
      background:rgba(20,184,166,.18);color:#2dd4bf;font-size:15px;font-weight:600;cursor:pointer;
      touch-action:manipulation`;
    closeBtn.onclick = () => closeTable(cell);
    cancelBtn.parentNode.insertBefore(closeBtn, cancelBtn);
  } else {
    // Close table for confirmed/pending occupied tables
    const btn = document.createElement("button");
    btn.id = "ts-close-table-btn";
    btn.textContent = t("close_table_btn");
    btn.style.cssText = `width:100%;padding:12px;border-radius:12px;border:none;margin-bottom:8px;
      background:rgba(20,184,166,.18);color:#2dd4bf;font-size:15px;font-weight:600;cursor:pointer;
      touch-action:manipulation`;
    btn.onclick = () => closeTable(cell);
    cancelBtn.parentNode.insertBefore(btn, cancelBtn);
  }
}

function showWalkInModal(cell) {
  haptic("impact");
  document.getElementById("__walkin-modal")?.remove();

  const info = TABLE_INFO[cell] || { cap: 4 };
  const guestOptions = Array.from({ length: info.cap }, (_, i) => i + 1)
    .map(n => `<button class="_wi-g" data-g="${n}" style="padding:8px 14px;border-radius:8px;border:1.5px solid rgba(255,255,255,.2);background:rgba(255,255,255,.07);color:#fff;font-size:15px;cursor:pointer">${n}</button>`)
    .join("");

  const overlay = document.createElement("div");
  overlay.id = "__walkin-modal";
  overlay.style.cssText = `position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,.75);
    display:flex;align-items:flex-end;justify-content:center`;
  overlay.innerHTML = `
    <div style="background:#1e1e2e;border-radius:20px 20px 0 0;padding:20px;width:100%;max-width:480px">
      <div style="font-size:15px;font-weight:700;margin-bottom:14px">${t("walkin_title", cell)}</div>
      <div style="font-size:12px;color:var(--c-muted);margin-bottom:8px">${t("walkin_guests_lbl")}</div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px" id="_wi-guests">${guestOptions}</div>
      <div style="font-size:12px;color:var(--c-muted);margin-bottom:6px">${t("walkin_name_lbl")}</div>
      <input id="_wi-name" type="text" placeholder="${t("walkin_name_ph")}"
        style="width:100%;box-sizing:border-box;padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,.15);
          background:rgba(255,255,255,.07);color:#fff;font-size:14px;margin-bottom:12px">
      <div style="font-size:12px;color:var(--c-muted);margin-bottom:6px">${t("walkin_comment_lbl")}</div>
      <input id="_wi-comment" type="text" placeholder="${t("walkin_comment_ph")}"
        style="width:100%;box-sizing:border-box;padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,.15);
          background:rgba(255,255,255,.07);color:#fff;font-size:14px;margin-bottom:16px">
      <button id="_wi-confirm" disabled
        style="width:100%;padding:13px;border-radius:12px;border:none;
          background:rgba(100,100,100,.3);color:#888;font-size:15px;font-weight:600;cursor:not-allowed;margin-bottom:8px">
        ${t("walkin_confirm")}
      </button>
      <button onclick="document.getElementById('__walkin-modal').remove()"
        style="width:100%;padding:11px;border-radius:12px;border:none;
          background:rgba(255,255,255,.08);color:#aaa;font-size:14px;cursor:pointer">
        ${t("walkin_cancel")}
      </button>
    </div>`;

  // Guest count selection
  let selectedGuests = null;
  overlay.querySelectorAll("._wi-g").forEach(btn => {
    btn.addEventListener("click", () => {
      overlay.querySelectorAll("._wi-g").forEach(b => {
        b.style.background = "rgba(255,255,255,.07)";
        b.style.borderColor = "rgba(255,255,255,.2)";
        b.style.color = "#fff";
      });
      btn.style.background   = "rgba(34,197,94,.25)";
      btn.style.borderColor  = "#22c55e";
      btn.style.color        = "#4ade80";
      selectedGuests = btn.dataset.g;
      const confirmBtn = overlay.querySelector("#_wi-confirm");
      confirmBtn.disabled = false;
      confirmBtn.style.background = "#22c55e";
      confirmBtn.style.color      = "#fff";
      confirmBtn.style.cursor     = "pointer";
    });
  });

  overlay.querySelector("#_wi-confirm").addEventListener("click", async () => {
    if (!selectedGuests) return;
    const name    = overlay.querySelector("#_wi-name").value.trim()    || t("walkin_name_ph");
    const comment = overlay.querySelector("#_wi-comment").value.trim() || "";
    overlay.remove();
    await doWalkIn(cell, selectedGuests, name, comment);
  });

  overlay.addEventListener("click", e => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
}

async function doWalkIn(cell, guestsCount, name, comment) {
  haptic("impact");
  try {
    const r = await fetchT("/api/staff/walkin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        init_data:    tg?.initData || "",
        hall:         liveHall,
        table:        cell,
        guests_count: guestsCount,
        name,
        comment,
      }),
    });
    const d = await r.json();
    if (d.ok) {
      toast(t("walkin_ok", cell, guestsCount));
      hideTableSheet();
      setTimeout(() => {
        loadLiveFloor();
        loadStaffPanel();
        if (state.step === 0) loadFloorPlan();
      }, 500);
    } else {
      toast(t("err_generic", d.detail || "?"), true);
    }
  } catch {
    toast(t("err_conn"), true);
  }
}

async function showSeatEnRouteModal(cell) {
  haptic("impact");
  document.getElementById("__seat-enroute-modal")?.remove();

  const overlay = document.createElement("div");
  overlay.id = "__seat-enroute-modal";
  overlay.style.cssText = `position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,.75);
    display:flex;align-items:flex-end;justify-content:center`;
  overlay.innerHTML = `
    <div style="background:#1e1e2e;border-radius:20px 20px 0 0;padding:20px;width:100%;max-width:480px;max-height:80vh;display:flex;flex-direction:column">
      <div style="font-size:15px;font-weight:700;margin-bottom:14px">${t("seat_enroute_title", cell)}</div>
      <div id="_ser-list" style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:8px;min-height:60px">
        <div style="color:var(--c-muted);font-size:13px;text-align:center;padding:20px 0">${t("loading")}</div>
      </div>
      <button onclick="document.getElementById('__seat-enroute-modal').remove()"
        style="width:100%;padding:11px;border-radius:12px;border:none;margin-top:14px;
          background:rgba(255,255,255,.08);color:#aaa;font-size:14px;cursor:pointer">
        ${t("walkin_cancel")}
      </button>
    </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });

  // Load en_route bookings
  try {
    const initData = encodeURIComponent(tg?.initData || "");
    const r = await fetchT(`/api/staff/enroute/today?init_data=${initData}`);
    const d = await r.json();
    const bookings = d.bookings || [];
    const listEl = document.getElementById("_ser-list");
    if (!listEl) return;

    if (bookings.length === 0) {
      listEl.innerHTML = `<div style="color:var(--c-muted);font-size:14px;text-align:center;padding:30px 0">${t("seat_enroute_empty")}</div>`;
      return;
    }

    listEl.innerHTML = "";
    bookings.forEach(b => {
      const card = document.createElement("div");
      card.style.cssText = `background:rgba(249,115,22,.1);border-radius:12px;padding:12px 14px;
        border-left:3px solid #f97316;cursor:pointer;transition:background .15s`;
      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
          <span style="font-weight:600;font-size:14px">👤 ${esc(b.name)}</span>
          <span style="font-size:12px;color:#fb923c;font-weight:600">${t("seat_enroute_guests", b.guests_count)}</span>
        </div>
        <div style="font-size:12px;color:var(--c-muted)">
          📞 ${esc(b.phone)} · ⏰ ${esc(b.time)}
          ${b.table && b.table !== "—" ? ` · 🪑 ${esc(b.table)}` : ""}
          ${b.comment ? `<br>💬 ${esc(b.comment)}` : ""}
        </div>
      `;
      card.addEventListener("mouseenter", () => { card.style.background = "rgba(249,115,22,.2)"; });
      card.addEventListener("mouseleave", () => { card.style.background = "rgba(249,115,22,.1)"; });
      card.addEventListener("click", async () => {
        haptic("impact");
        card.style.pointerEvents = "none";
        card.style.opacity = "0.5";
        try {
          const resp = await fetchT("/api/staff/enroute/seat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              init_data: tg?.initData || "",
              booking_id: b.id,
              table: cell,
              hall: liveHall,
            }),
          });
          const rd = await resp.json();
          if (rd.ok) {
            toast(t("seat_enroute_ok", b.name, cell));
            overlay.remove();
            hideTableSheet();
            setTimeout(() => {
              loadLiveFloor();
              loadStaffPanel();
              if (state.step === 0) loadFloorPlan();
            }, 500);
          } else {
            toast(t("err_generic", rd.detail || "?"), true);
            card.style.pointerEvents = "";
            card.style.opacity = "";
          }
        } catch {
          toast(t("err_conn"), true);
          card.style.pointerEvents = "";
          card.style.opacity = "";
        }
      });
      listEl.appendChild(card);
    });
  } catch {
    const listEl = document.getElementById("_ser-list");
    if (listEl) listEl.innerHTML = `<div style="color:var(--c-muted);font-size:13px;text-align:center;padding:20px 0">${t("error_load")}</div>`;
  }
}

async function closeTable(cell) {
  const ok = await tgConfirm(t("close_table_confirm", cell));
  if (!ok) return;
  haptic("impact");
  const date = getVNDateISO();
  try {
    const r = await fetchT("/api/staff/table/close", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        init_data: tg?.initData || "",
        hall:      liveHall,
        table:     cell,
        date,
      }),
    });
    const d = await r.json();
    if (d.ok) {
      toast(t("close_table_ok", cell));
      hideTableSheet();
      setTimeout(() => {
        loadLiveFloor();
        loadStaffPanel();
        if (state.step === 0) loadFloorPlan();
      }, 500);
    } else {
      toast(t("err_generic", d.detail || "?"), true);
    }
  } catch {
    toast(t("err_conn"), true);
  }
}

async function cancelBookingInSheet(bookingId, cell) {
  const ok = await tgConfirm(t("ts_cancel_booking"));
  if (!ok) return;
  haptic("impact");
  try {
    const r = await fetchT("/api/staff/booking/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: tg?.initData || "", booking_id: bookingId }),
    });
    const d = await r.json();
    if (d.ok) {
      toast(t("ts_booking_cancelled"));
      _loadTableBookings(cell);
      setTimeout(() => {
        loadLiveFloor();
        loadStaffPanel();
        if (state.step === 0) loadFloorPlan();
      }, 600);
    } else {
      toast(t("err_generic", d.detail || "?"), true);
    }
  } catch (e) {
    toast(t("err_conn"), true);
  }
}

async function arrivedBookingInSheet(bookingId, cell) {
  const ok = await tgConfirm(t("ts_arrived_confirm"));
  if (!ok) return;
  haptic("impact");
  try {
    const r = await fetchT("/api/staff/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: tg?.initData || "", booking_id: bookingId, action: "arrived" }),
    });
    const d = await r.json();
    if (r.ok) {
      toast("✅ " + t("status_confirmed"));
      _loadTableBookings(cell);
      setTimeout(() => {
        loadLiveFloor();
        loadStaffPanel();
        if (state.step === 0) loadFloorPlan();
      }, 600);
    } else {
      toast(t("err_generic", d.detail || "?"), true);
    }
  } catch {
    toast(t("err_conn"), true);
  }
}

async function showMovePicker(bookingId, currentTable) {
  haptic("sel");
  // Fetch current live table statuses for BOTH halls in parallel
  const date = getVNDateISO();
  const now  = new Date();
  const vnStr = now.toLocaleTimeString("en-GB", { timeZone: "Asia/Ho_Chi_Minh" });
  const [hh, mm] = vnStr.split(":").map(Number);
  const cur_min  = (hh <= 2 ? hh + 24 : hh) * 60 + mm;
  const otherHall = liveHall === "main" ? "second" : "main";
  let liveStatusesCurrent = {}, liveStatusesOther = {};
  try {
    const [r1, r2] = await Promise.all([
      fetchT(`/api/tables/live?hall=${liveHall}&date=${date}&current_minutes=${cur_min}`),
      fetchT(`/api/tables/live?hall=${otherHall}&date=${date}&current_minutes=${cur_min}`),
    ]);
    liveStatusesCurrent = (await r1.json()).tables || {};
    liveStatusesOther   = (await r2.json()).tables || {};
  } catch {}

  const STATUS_BG     = { free: "rgba(34,197,94,.2)", pending: "rgba(168,85,247,.2)", en_route: "rgba(249,115,22,.2)", confirmed: "rgba(220,50,50,.2)" };
  const STATUS_BORDER = { free: "#22c55e", pending: "#a855f7", en_route: "#f97316", confirmed: "#e05b5b" };
  const STATUS_LABEL  = { free: t("leg_free"), pending: t("leg_pend"), en_route: t("leg_enroute"), confirmed: t("leg_busy") };
  const validTableIds = new Set(Object.keys(TABLE_INFO));

  function buildButtons(layoutKey, statuses, excludeTable) {
    const layout = LAYOUTS[layoutKey];
    const ids = Object.keys(layout.tables || {}).filter(id =>
      id !== excludeTable && validTableIds.has(id)
    );
    return ids.map(id => {
      const s    = statuses[id]?.status || "free";
      const info = TABLE_INFO[id] || { icon: "🪑", cap: 2 };
      return `<button onclick="doMoveBooking(${bookingId},'${id}','${layoutKey}')"
        style="padding:10px 8px;border-radius:10px;border:1.5px solid ${STATUS_BORDER[s]};
          background:${STATUS_BG[s]};cursor:pointer;display:flex;flex-direction:column;
          align-items:center;gap:3px;min-width:60px">
        <span style="font-size:18px">${info.icon}</span>
        <span style="font-size:12px;font-weight:600;color:#fff">${t("table_prefix")} ${id}</span>
        <span style="font-size:10px;color:${STATUS_BORDER[s]}">${STATUS_LABEL[s]}</span>
      </button>`;
    }).join("");
  }

  const currentButtons = buildButtons(liveHall, liveStatusesCurrent, currentTable);
  const otherButtons   = buildButtons(otherHall, liveStatusesOther, null);

  // Build overlay
  document.getElementById("__move-picker")?.remove();
  const overlay = document.createElement("div");
  overlay.id = "__move-picker";
  overlay.style.cssText = `position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.7);
    display:flex;align-items:flex-end;justify-content:center`;

  overlay.innerHTML = `
    <div style="background:#1e1e2e;border-radius:20px 20px 0 0;padding:20px;width:100%;max-width:480px;max-height:75vh;overflow-y:auto">
      <div style="font-size:15px;font-weight:700;margin-bottom:16px">${t("move_title")}</div>

      <div style="font-size:12px;color:var(--c-muted);font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px">
        ${LAYOUTS[liveHall]?.hallLabel || liveHall}
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px">
        ${currentButtons || '<div style="color:var(--c-muted);font-size:13px">' + t("move_no_tables") + '</div>'}
      </div>

      <div style="height:1px;background:rgba(255,255,255,.1);margin:0 0 14px"></div>

      <div style="font-size:12px;color:#a78bfa;font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px">
        ${t("move_other_floor", LAYOUTS[otherHall]?.hallLabel || otherHall)}
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px">
        ${otherButtons || '<div style="color:var(--c-muted);font-size:13px">' + t("move_no_tables") + '</div>'}
      </div>

      <button onclick="document.getElementById('__move-picker').remove()"
        style="width:100%;padding:10px;border-radius:10px;border:none;
          background:rgba(255,255,255,.1);color:#aaa;cursor:pointer;font-size:14px">${t("move_cancel")}</button>
    </div>`;

  overlay.addEventListener("click", e => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
}

async function doMoveBooking(bookingId, newTable, newHall) {
  document.getElementById("__move-picker")?.remove();
  haptic("impact");
  try {
    const payload = { init_data: tg?.initData || "", booking_id: bookingId, new_table: newTable };
    if (newHall && newHall !== liveHall) payload.new_hall = newHall;
    const r = await fetchT("/api/staff/booking/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const d = await r.json();
    if (d.ok) {
      const hallSuffix = newHall && newHall !== liveHall
        ? ` · ${LAYOUTS[newHall]?.hallLabel || newHall}` : "";
      toast(t("move_ok", newTable, hallSuffix));
      if (_sheetCell) _loadTableBookings(_sheetCell);
      setTimeout(() => {
        loadLiveFloor();
        loadStaffPanel();
        if (state.step === 0) loadFloorPlan();
      }, 600);
    } else {
      toast(t("err_generic", d.detail || "?"), true);
    }
  } catch {
    toast(t("err_conn"), true);
  }
}

function hideTableSheet() {
  const sheet = document.getElementById("table-sheet");
  sheet.classList.remove("open");
  setTimeout(() => { sheet.style.display = "none"; }, 320);
}

document.getElementById("ts-confirm")?.addEventListener("click", () => {
  if (_sheetLiveMode) {
    // Switch to booking tab and pre-select this table, then go to date/time step
    state.table = _sheetPending;
    hideTableSheet();
    haptic("impact");
    setActiveTab(tabBook);
    showView(bookView);
    stopStaffRefresh(); stopTablesRefresh();
    goTo(1);  // table already selected — go straight to date/time
  } else {
    state.table = _sheetPending;
    hideTableSheet();
    haptic("impact");
    renderFloorPlan();
    updateSelBadge();
  }
});
document.getElementById("ts-cancel")?.addEventListener("click", hideTableSheet);
document.getElementById("ts-overlay")?.addEventListener("click", hideTableSheet);

function startRefresh() {
  stopRefresh();
  loadFloorPlan();
  refreshTimer = setInterval(loadFloorPlan, 15_000);
}
function stopRefresh() {
  if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
}

document.getElementById("btn-to-form").addEventListener("click", () => {
  if (!state.date) { toast(t("toast_sel_date"), true); return; }
  if (!state.time) { toast(t("toast_sel_time"), true); return; }
  haptic("impact");
  goTo(2);
});

/* ─────────── SCREEN 2: FORM ─────────── */
function fillFormMeta() {
  document.getElementById("p-hall").textContent  = hallLabel(state.hall);
  document.getElementById("p-table").textContent = `${t("table_prefix")} ${state.table}`;
  document.getElementById("p-date").textContent  = fmtDate(state.date);
  document.getElementById("p-time").textContent  = state.time;

  // Deposit banner
  const info      = TABLE_INFO[state.table];
  const depBanner = document.getElementById("deposit-banner");
  if (depBanner && info) {
    const depAmountEl = document.getElementById("dep-amount");
    if (info.deposit > 0) {
      depBanner.style.display = "";
      depAmountEl.textContent  = info.deposit.toLocaleString("ru-RU") + " ₫";
    } else {
      depBanner.style.display = "none";
    }
    // Capacity hint
    const capHint = document.getElementById("cap-hint");
    if (capHint) capHint.textContent = t("cap_hint", info.cap);
  } else if (depBanner) {
    depBanner.style.display = "none";
  }

  // Pre-fill from guest selected in Regulars tab (admin flow)
  const nameInp  = document.getElementById("name-input");
  const phoneInp = document.getElementById("phone-input");
  if (state.prefilledGuest) {
    nameInp.value  = state.prefilledGuest.name  || "";
    phoneInp.value = state.prefilledGuest.phone || "";
    // Lookup VIP banner for pre-filled guest
    if (state.prefilledGuest.phone) {
      fetch(`/api/guest?phone=${encodeURIComponent(state.prefilledGuest.phone)}`)
        .then(r => r.json()).then(g => { if (g.found) showGuestBanner(g); }).catch(() => {});
    }
    state.prefilledGuest = null;
  } else {
    // Pre-fill Telegram name and username for regular users
    const tgUser = tg?.initDataUnsafe?.user;
    if (tgUser && !nameInp.value) {
      nameInp.value = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(" ");
    }
    if (tgUser?.username) {
      const tgInp = document.getElementById("tg-input");
      if (tgInp && !tgInp.value) tgInp.value = "@" + tgUser.username;
    }
  }
}

// Guest count chips
document.querySelectorAll(".chip").forEach(c => {
  c.addEventListener("click", () => {
    document.querySelectorAll(".chip").forEach(x => x.classList.remove("sel"));
    c.classList.add("sel");
    state.guests = c.dataset.n;
    haptic("sel");
    // Capacity check
    const info = TABLE_INFO[state.table];
    if (info) {
      const gNum = parseInt(state.guests) || (state.guests === "6+" ? 6 : 0);
      if (gNum > info.cap) {
        toast(t("toast_cap_warn", state.table, info.cap), true);
      }
    }
  });
});

// Phone lookup
const phoneInput = document.getElementById("phone-input");
phoneInput.addEventListener("blur", async () => {
  const phone = phoneInput.value.trim();
  if (phone.length < 7) return;
  try {
    const r = await fetch(`/api/guest?phone=${encodeURIComponent(phone)}`);
    const g = await r.json();
    if (g.found) {
      const nameInp = document.getElementById("name-input");
      if (!nameInp.value) nameInp.value = g.name || "";
      showGuestBanner(g);
    } else {
      hideGuestBanner();
    }
  } catch {}
});

function showGuestBanner(g) {
  const banner = document.getElementById("guest-banner");
  const badge  = document.getElementById("guest-badge");
  const name   = document.getElementById("guest-name-found");
  const visits = document.getElementById("guest-visits");
  const vip    = g.is_vip;

  badge.textContent  = vip ? "👑" : "👤";
  name.textContent   = (vip ? t("guest_vip") : "") + (g.name || "");
  const v = g.total_visits || 0;
  visits.textContent = t("guest_visits", v);
  banner.style.display = "flex";
}
function hideGuestBanner() {
  document.getElementById("guest-banner").style.display = "none";
}

// Submit
document.getElementById("btn-submit").addEventListener("click", submitBooking);
async function submitBooking() {
  const name      = document.getElementById("name-input").value.trim();
  const phone     = phoneInput.value.trim();
  const tgRaw     = document.getElementById("tg-input")?.value.trim() || "";
  const tgUsername = tgRaw ? (tgRaw.startsWith("@") ? tgRaw : "@" + tgRaw) : "";
  const comment   = document.getElementById("comment-input").value.trim();

  if (!name)        { toast(t("toast_enter_name"), true);          haptic("notify","error"); return; }
  if (!phone)       { toast(t("toast_enter_phone"), true);         haptic("notify","error"); return; }
  if (!state.guests){ toast(t("toast_enter_guests"), true);        haptic("notify","error"); return; }

  // Capacity validation
  const tblInfo = TABLE_INFO[state.table];
  if (tblInfo) {
    const gNum = parseInt(state.guests) || (state.guests === "6+" ? 6 : 0);
    if (gNum > tblInfo.cap) {
      toast(t("toast_cap_err", state.table, tblInfo.cap), true);
      haptic("notify","error");
      return;
    }
  }

  spinner(true);
  try {
    const body = {
      hall:         state.hall,
      date:         state.date,
      time:         state.time,
      table:        state.table,
      guests_count: state.guests,
      name,
      phone,
      tg_username:  tgUsername,
      comment,
      init_data: tg?.initData || "",
    };
    const r = await fetch("/api/book", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const d = await r.json();
    if (!r.ok) {
      // Check if this is a blacklist block
      const detail = d.detail || "";
      if (r.status === 403 && detail.startsWith("blacklisted")) {
        const reason = detail.replace(/^blacklisted\s*/, "").replace(/^\(|\)$/g, "").trim();
        toast(t("bl_blocked_msg", reason), true);
      } else {
        toast(detail || t("toast_book_err"), true);
      }
      haptic("notify","error");
    } else {
      state.name  = name;
      state.phone = phone;
      haptic("notify","success");
      fillSuccess(d);
      goTo(3);
    }
  } catch {
    toast(t("toast_no_conn"), true);
    haptic("notify","error");
  } finally {
    spinner(false);
  }
}

function fillSuccess(d) {
  const guestName  = state.name  || document.getElementById("name-input").value.trim();
  const guestPhone = state.phone || phoneInput.value.trim();
  const info       = TABLE_INFO[state.table];
  const depLine    = info?.deposit > 0
    ? `<br><b>💳 ${t("lbl_deposit")}:</b> <span style="color:var(--c-amber)">${info.deposit.toLocaleString("ru-RU")} ₫</span>`
    : "";
  const noteLine   = info?.note ? `<br><small style="color:var(--c-sub)">${info.icon} ${info.note}</small>` : "";

  document.getElementById("done-text").textContent = t("done_sub");
  document.getElementById("done-card").innerHTML = `
    <b>${t("lbl_hall")}:</b> ${hallLabel(state.hall)}<br>
    <b>${t("lbl_table")}:</b> ${state.table}${noteLine}<br>
    <b>${t("lbl_date")}:</b> ${fmtDate(state.date)}<br>
    <b>${t("lbl_time")}:</b> ${state.time}<br>
    <b>${t("lbl_guests")}:</b> ${state.guests}<br>
    <b>${t("lbl_name")}:</b> ${guestName}<br>
    <b>${t("lbl_phone")}:</b> ${guestPhone}${depLine}
  `.trim();
}

/* ─────────── GLOBAL BACK ─────────── */
document.getElementById("global-back").addEventListener("click", () => {
  if (state.step > 0 && state.step < 3) {
    haptic("impact","light");
    goTo(state.step - 1);
  }
});

/* ─────────── MY BOOKINGS SHEET (guest) ─────────── */
function showMyBookingsSheet(phone) {
  const sheet = document.getElementById("my-bookings-sheet");
  const list  = document.getElementById("my-bookings-list");
  list.innerHTML = `<div class="muted-text" style="text-align:center;padding:30px 0">${t("mbs_loading")}</div>`;
  sheet.style.display = "flex";
  requestAnimationFrame(() => sheet.classList.add("open"));
  loadMyBookings(phone);
}
function hideMyBookingsSheet() {
  const sheet = document.getElementById("my-bookings-sheet");
  sheet.classList.remove("open");
  setTimeout(() => { sheet.style.display = "none"; }, 320);
}
async function loadMyBookings(phone) {
  const list = document.getElementById("my-bookings-list");
  try {
    const r = await fetchT(`/api/my/bookings?phone=${encodeURIComponent(phone)}`);
    const d = await r.json();
    renderMyBookings(d.bookings || []);
  } catch {
    list.innerHTML = `<div class="muted-text" style="text-align:center;padding:20px 0">${t("mbs_error")}</div>`;
  }
}
function renderMyBookings(bookings) {
  const list = document.getElementById("my-bookings-list");
  if (!bookings.length) {
    list.innerHTML = `<div class="muted-text" style="text-align:center;padding:30px 0">${t("mbs_empty")}</div>`;
    return;
  }
  list.innerHTML = "";
  const STATUS = { pending: t("status_pending"), confirmed: t("status_confirmed"), en_route: t("status_en_route"), cancelled: t("status_cancelled") };
  bookings.forEach(b => {
    const card = document.createElement("div");
    card.className = `staff-card status-${b.status}`;
    const statusLabel = STATUS[b.status] || b.status;
    card.innerHTML = `
      <div class="sc-top">
        <div class="sc-name">${t("table_prefix")} ${esc(b.table || "—")}</div>
        <div class="sc-status ${b.status}">${statusLabel}</div>
      </div>
      <div class="sc-meta">
        🏛 ${esc(b.hall_label || b.hall)} · <b>${t("table_prefix")} ${esc(b.table || "—")}</b><br>
        📅 ${fmtDate(b.date)} · <b>${esc(b.time)}</b><br>
        👥 ${t("guests_lbl")} <b>${esc(String(b.guests_count || "—"))}</b>
      </div>
    `;
    list.appendChild(card);
  });
}

// Close guest sheet
document.getElementById("mbs-overlay")?.addEventListener("click", hideMyBookingsSheet);
document.getElementById("mbs-close")?.addEventListener("click", hideMyBookingsSheet);

// “Перейти к бронированиям” button on success screen
document.getElementById("btn-go-bookings").addEventListener("click", () => {
  haptic("impact");
  if (isStaff) {
    // Staff: switch to staff panel tab
    setActiveTab(tabStaff);
    showView(staffView);
    stopRefresh(); stopTablesRefresh();
    loadStaffPanel(); startStaffRefresh();
  } else {
    // Guest: show read-only booking status sheet
    const phone = document.getElementById("phone-input")?.value.trim() || state.phone;
    showMyBookingsSheet(phone);
  }
});

/* ─────────── TAB BAR ─────────── */
const tabBook      = document.getElementById("tab-book");
const tabStaff     = document.getElementById("tab-staff-btn");
const tabTables    = document.getElementById("tab-tables-btn");
const tabRegulars  = document.getElementById("tab-regulars-btn");
const bookView     = document.getElementById("booking-view");
const staffView    = document.getElementById("staff-view");
const tablesView   = document.getElementById("tables-view");
const regularsView = document.getElementById("regulars-view");

function setActiveTab(activeBtn) {
  [tabBook, tabStaff, tabTables, tabRegulars].forEach(b => b?.classList.remove("active"));
  activeBtn?.classList.add("active");
}
function showView(v) {
  [bookView, staffView, tablesView, regularsView].forEach(el => { if (el) el.style.display = "none"; });
  if (v) v.style.display = "flex";
}

tabBook.addEventListener("click", () => {
  setActiveTab(tabBook);
  showView(bookView);
  stopStaffRefresh(); stopTablesRefresh(); stopCountdown(); stopLiveCountdown();
  if (state.step === 0) startRefresh();
  haptic("sel");
});

tabStaff.addEventListener("click", () => {
  setActiveTab(tabStaff);
  showView(staffView);
  stopRefresh(); stopTablesRefresh(); stopCountdown(); stopLiveCountdown();
  loadStaffPanel(); startStaffRefresh();
  haptic("sel");
});

tabTables.addEventListener("click", () => {
  setActiveTab(tabTables);
  showView(tablesView);
  stopRefresh(); stopStaffRefresh(); stopCountdown();
  loadLiveFloor(); startTablesRefresh();
  haptic("sel");
});

tabRegulars?.addEventListener("click", () => {
  setActiveTab(tabRegulars);
  showView(regularsView);
  stopRefresh(); stopStaffRefresh(); stopTablesRefresh(); stopCountdown(); stopLiveCountdown();
  // Reset to guests sub-panel
  const pgDiv = document.getElementById("reg-panel-guests");
  const pbDiv = document.getElementById("reg-panel-blacklist");
  if (pgDiv) pgDiv.style.display = "";
  if (pbDiv) pbDiv.style.display = "none";
  document.getElementById("reg-subtab-guests")?.classList.add("active");
  document.getElementById("reg-subtab-blacklist")?.classList.remove("active");
  document.getElementById("regulars-add").style.display = "";
  loadRegulars();
  haptic("sel");
});

document.getElementById("staff-refresh").addEventListener("click", () => {
  loadStaffPanel();
  haptic("impact","light");
});

// Staff filter buttons
const _filterIds = ["filter-pending", "filter-confirmed", "filter-enroute"];
function _setActiveFilter(activeId) {
  _filterIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle("active", id === activeId);
  });
}
document.getElementById("filter-pending").addEventListener("click", () => {
  staffFilter = "pending";
  _setActiveFilter("filter-pending");
  document.getElementById("staff-title").textContent = t("staff_title_pending");
  loadStaffPanel();
});
document.getElementById("filter-confirmed").addEventListener("click", () => {
  staffFilter = "confirmed_today";
  _setActiveFilter("filter-confirmed");
  document.getElementById("staff-title").textContent = t("staff_title_confirmed");
  loadStaffPanel();
});
document.getElementById("filter-enroute").addEventListener("click", () => {
  staffFilter = "en_route";
  _setActiveFilter("filter-enroute");
  document.getElementById("staff-title").textContent = t("staff_title_en_route");
  loadStaffPanel();
});
// occupied tab removed — en_route tab replaces it

/* ─────────── STAFF PANEL ─────────── */
async function loadStaffPanel() {
  const list = document.getElementById("staff-list");
  list.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("loading")}</div>`;
  // occupied filter removed
  try {
    const initData = encodeURIComponent(tg?.initData || "");
    const r = await fetchT(`/api/staff/bookings?init_data=${initData}&date_filter=${staffFilter}`);
    if (r.status === 403) {
      list.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("staff_forbidden")}</div>`;
      return;
    }
    const d = await r.json();
    const bookings = d.bookings || [];
    const pendingCount = d.pending_count ?? bookings.filter(b => b.status === "pending").length;
    const en_route_count = d.en_route_count ?? 0;
    _staffBookingsCache = { bookings, filter: staffFilter, pendingCount };
    renderStaffList(bookings);

    // Sub-label
    if (staffFilter === "pending") {
      document.getElementById("staff-count").textContent =
        bookings.length === 0 ? t("staff_count_pending_0") : t("staff_count_pending_n", bookings.length);
    } else if (staffFilter === "en_route") {
      document.getElementById("staff-count").textContent =
        bookings.length === 0 ? t("staff_count_en_route_0") : t("staff_count_en_route_n", bookings.length);
    } else {
      document.getElementById("staff-count").textContent =
        bookings.length === 0 ? t("staff_count_confirmed_0") : t("staff_count_confirmed_n", bookings.length);
    }

    // Tab badge (main tab icon) — always reflects pending count
    const badge = document.getElementById("tab-badge");
    badge.textContent = pendingCount > 9 ? "9+" : String(pendingCount);
    badge.style.display = pendingCount > 0 ? "flex" : "none";

    // Filter badge inside the "Ожидают" button
    const fbadge = document.getElementById("filter-pending-badge");
    fbadge.textContent = pendingCount > 9 ? "9+" : String(pendingCount);
    fbadge.style.display = pendingCount > 0 ? "inline-flex" : "none";

    // En-route badge — always shows real count from server
    const enBadge = document.getElementById("filter-enroute-badge");
    if (enBadge) {
      enBadge.textContent = en_route_count > 9 ? "9+" : String(en_route_count);
      enBadge.style.display = en_route_count > 0 ? "inline-flex" : "none";
    }
  } catch {
    list.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("error_load")}</div>`;
  }
}

/* ─────────── PENDING COUNTDOWN TIMER ─────────── */
const PENDING_WINDOW_MS = 15 * 60 * 1000; // 15 minutes
let _countdownTimer = null;

function startCountdown() {
  stopCountdown();
  _countdownTimer = setInterval(_tickCountdowns, 1000);
}
function stopCountdown() {
  if (_countdownTimer) { clearInterval(_countdownTimer); _countdownTimer = null; }
}

function _tickCountdowns() {
  const els = document.querySelectorAll(".sc-countdown[data-created-at]");
  if (!els.length) { stopCountdown(); return; }
  let anyExpired = false;
  const nowMs = Date.now();
  els.forEach(el => {
    const createdAt = el.dataset.createdAt;
    if (!createdAt) return;
    // created_at is UTC ISO from server; convert to ms
    const createdMs = new Date(createdAt.endsWith("Z") ? createdAt : createdAt + "Z").getTime();
    const elapsedMs  = nowMs - createdMs;
    const remainMs   = PENDING_WINDOW_MS - elapsedMs;
    if (remainMs <= 0) {
      el.textContent = t("timeout_lbl");
      el.className = "sc-countdown sc-countdown-expired";
      anyExpired = true;
    } else {
      const totalSec = Math.ceil(remainMs / 1000);
      const m = Math.floor(totalSec / 60);
      const s = totalSec % 60;
      el.textContent = `⏱ ${m}:${String(s).padStart(2,"0")}`;
      el.className = "sc-countdown" + (
        remainMs < 2 * 60_000 ? " sc-countdown-red"
        : remainMs < 5 * 60_000 ? " sc-countdown-amber"
        : " sc-countdown-green"
      );
    }
  });
  if (anyExpired) {
    stopCountdown();
    setTimeout(() => loadStaffPanel(), 1500); // short pause so user sees "expired" flash
  }
}

function renderStaffList(bookings) {
  stopCountdown();
  stopOccupiedCountdown();
  // Client-side guard: enforce correct status filter regardless of server response
  if (staffFilter === "pending") {
    bookings = bookings.filter(b => b.status === "pending");
  } else if (staffFilter === "confirmed_today") {
    bookings = bookings.filter(b => b.status === "confirmed");
  } else if (staffFilter === "en_route") {
    bookings = bookings.filter(b => b.status === "en_route");
  }
  const list = document.getElementById("staff-list");
  if (!bookings.length) {
    const emptyMsg = staffFilter === "pending"
      ? t("staff_empty_pending")
      : staffFilter === "en_route"
      ? t("staff_empty_en_route")
      : t("staff_empty_confirmed");
    list.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${emptyMsg}</div>`;
    return;
  }
  list.innerHTML = "";
  bookings.forEach(b => {
    const card = document.createElement("div");
    card.className = `staff-card status-${b.status}`;

    const statusLabel = { pending:t("status_pending"), confirmed:t("status_confirmed"), en_route:t("status_en_route"), cancelled:t("status_cancelled") }[b.status] || b.status;
    // Action buttons only for staff/admin users
    const canAct = isStaff && b.status === "pending";
    const canArrive = isStaff && b.status === "en_route";
    const isPending = b.status === "pending";
    const isEnRoute = b.status === "en_route";

    // Build Telegram contact button for all booking cards (pending, confirmed, en_route)
    const tgHandle = b.tg_username ? b.tg_username.replace(/^@/, '') : '';
    const tgUserId = b.tg_user_id || 0;
    let tgBtnHtml = '';
    if (tgHandle) {
      tgBtnHtml = `<a href="https://t.me/${tgHandle}" target="_blank" style="display:flex;align-items:center;justify-content:center;gap:5px;padding:8px 10px;border-radius:8px;background:rgba(41,182,246,.18);color:#7dd3f8;font-size:13px;font-weight:600;text-decoration:none;margin-top:6px">✈️ @${tgHandle}</a>`;
    } else if (tgUserId) {
      tgBtnHtml = `<a href="tg://user?id=${tgUserId}" style="display:flex;align-items:center;justify-content:center;gap:5px;padding:8px 10px;border-radius:8px;background:rgba(41,182,246,.18);color:#7dd3f8;font-size:13px;font-weight:600;text-decoration:none;margin-top:6px">✈️ Написать в Telegram</a>`;
    }

    card.innerHTML = `
      <div class="sc-top">
        <div class="sc-name">${esc(b.name || b.guest_name || "—")}</div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
          <div class="sc-status ${b.status}${isPending ? " sc-status-pulse" : ""}">${
            isPending ? t("ts_live_pend") : isEnRoute ? t("ts_live_enroute") : statusLabel
          }</div>
          ${isPending && b.created_at ? `<span class="sc-countdown sc-countdown-green" data-created-at="${esc(b.created_at)}">⏱ …</span>` : ""}
        </div>
      </div>
      <div class="sc-meta">
        📞 <b>${esc(b.phone || "—")}</b><br>
        🏛 ${esc(b.hall_label || b.hall)} · <b>${t("table_prefix")} ${esc(b.table || "—")}</b><br>
        📅 ${fmtDate(b.date)} · <b>${esc(b.time)}</b><br>
        👥 ${t("guests_lbl")} <b>${esc(String(b.guests_count || b.guests || "—"))}</b>
        ${b.comment ? `<br>💬 ${esc(b.comment)}` : ""}
        ${b.is_vip   ? " 👑 VIP" : ""}
      </div>
      ${tgBtnHtml}
      ${canAct ? `
      <div class="sc-actions">
        <button class="sc-btn confirm" data-id="${b.id}" data-act="confirm">${t("btn_confirm")}</button>
        <button class="sc-btn cancel"  data-id="${b.id}" data-act="cancel" >${t("btn_reject")}</button>
      </div>` : ""}
      ${canArrive ? `
      <div class="sc-arrive-label">${t("ts_live_enroute")} — ${t("table_prefix")} ${esc(b.table || "—")} · 👥 ${t("guests_lbl")} ${esc(String(b.guests_count || "—"))}</div>
      <div class="sc-actions">
        <button class="sc-btn confirm" data-id="${b.id}" data-act="arrived">${t("btn_arrived_yes")}</button>
        <button class="sc-btn cancel"  data-id="${b.id}" data-act="cancel" >${t("btn_arrived_no")}</button>
      </div>` : ""}
    `;

    if (canAct || canArrive) {
      card.querySelectorAll(".sc-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          btn.disabled = true;
          haptic("impact");
          await staffAction(b.id, btn.dataset.act);
          loadStaffPanel();
        });
      });
    }

    list.appendChild(card);
  });

  // Start countdown ticking for pending bookings
  if (staffFilter === "pending" && bookings.some(b => b.status === "pending")) {
    _tickCountdowns(); // immediate first tick (no 1s delay)
    startCountdown();
  }
}

function esc(str) {
  return String(str)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

/* ─────────── OCCUPIED TABLES (staff panel tab) ─────────── */
let _occCountTimer = null;
function startOccupiedCountdown() {
  stopOccupiedCountdown();
  _occCountTimer = setInterval(_tickOccupiedCountdowns, 1000);
}
function stopOccupiedCountdown() {
  if (_occCountTimer) { clearInterval(_occCountTimer); _occCountTimer = null; }
}
function _tickOccupiedCountdowns() {
  const els = document.querySelectorAll(".occ-remain[data-remain-sec]");
  if (!els.length) { stopOccupiedCountdown(); return; }
  let anyExpired = false;
  els.forEach(el => {
    let sec = parseInt(el.dataset.remainSec) - 1;
    if (sec < 0) sec = 0;
    el.dataset.remainSec = sec;
    el.textContent = _fmtRemain(sec);
    if      (sec <= 600)  el.className = "occ-remain tbl-remain-red";
    else if (sec <= 1800) el.className = "occ-remain tbl-remain-amber";
    else                  el.className = "occ-remain";
    if (sec === 0) anyExpired = true;
  });
  if (anyExpired) {
    stopOccupiedCountdown();
    setTimeout(() => loadStaffPanel(), 1500);
  }
}

async function loadOccupiedTables() {
  const list = document.getElementById("staff-list");
  try {
    const now    = new Date();
    const date   = getVNDateISO();
    const vnStr  = now.toLocaleTimeString("en-GB", { timeZone: "Asia/Ho_Chi_Minh", hour: "2-digit", minute: "2-digit" });
    const [hh, mm] = vnStr.split(":").map(Number);
    const adjH   = hh <= 2 ? hh + 24 : hh;
    const currentMinutes = adjH * 60 + mm;

    const [rMain, rSecond] = await Promise.all([
      fetchT(`/api/tables/live?hall=main&date=${date}&current_minutes=${currentMinutes}`),
      fetchT(`/api/tables/live?hall=second&date=${date}&current_minutes=${currentMinutes}`),
    ]);
    const dMain   = await rMain.json();
    const dSecond = await rSecond.json();

    const occupied = [];
    for (const [hall, d] of [["main", dMain], ["second", dSecond]]) {
      const tables = d.tables || {};
      for (const [tableId, info] of Object.entries(tables)) {
        if (info.status !== "free") {
          occupied.push({
            hall,
            tableId,
            status: info.status,
            remainingMin: info.remaining_min || 0,
            cap: TABLE_INFO[tableId]?.cap || 0,
          });
        }
      }
    }
    // Sort: pending first, then by remaining_min ascending
    occupied.sort((a, b) => {
      if (a.status !== b.status) return a.status === "pending" ? -1 : 1;
      return a.remainingMin - b.remainingMin;
    });

    document.getElementById("staff-count").textContent =
      occupied.length === 0 ? t("occ_count_0") : t("occ_count_n", occupied.length);

    const obadge = document.getElementById("filter-occupied-badge");
    obadge.textContent = occupied.length > 9 ? "9+" : String(occupied.length);
    obadge.style.display = occupied.length > 0 ? "inline-flex" : "none";

    _occupiedItemsCache = occupied;
    renderOccupiedTables(occupied);
  } catch {
    list.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("error_load")}</div>`;
  }
}

function renderOccupiedTables(items) {
  stopOccupiedCountdown();
  const list = document.getElementById("staff-list");
  if (!items.length) {
    list.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("occ_all_free")}</div>`;
    return;
  }
  list.innerHTML = "";
  items.forEach(item => {
    const card = document.createElement("div");
    card.className = `staff-card occ-card status-${item.status}`;
    const statusLabel = item.status === "pending" ? t("occ_status_pending") : item.status === "en_route" ? t("occ_status_en_route") : t("occ_status_confirmed");
    const remainSec   = item.remainingMin * 60;
    const remainCls   = remainSec > 0 ? (remainSec <= 600 ? " tbl-remain-red" : remainSec <= 1800 ? " tbl-remain-amber" : "") : "";
    card.innerHTML = `
      <div class="sc-top">
        <div style="display:flex;align-items:center;gap:10px">
          <span class="occ-table-badge status-${item.status}">${esc(item.tableId)}</span>
          <div>
            <div class="sc-name" style="margin:0">${t("table_prefix")} ${esc(item.tableId)}</div>
            <div class="occ-hall-label">${t("hall_label_" + item.hall)}${item.cap > 0 ? " · " + t("guests_pax",item.cap) : ""}</div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px">
          <div class="sc-status ${item.status === "pending" ? "pending sc-status-pulse" : item.status === "en_route" ? "en_route" : "confirmed"}">${statusLabel}</div>
          ${remainSec > 0 ? `<span class="occ-remain${remainCls}" data-remain-sec="${remainSec}">${t("remain_soon")} ${_fmtRemain(remainSec)}</span>` : ""}
        </div>
      </div>
    `;
    list.appendChild(card);
  });
  if (items.some(i => i.remainingMin > 0)) {
    _tickOccupiedCountdowns();
    startOccupiedCountdown();
  }
}

async function staffAction(bookingId, action) {
  try {
    const r = await fetch("/api/staff/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: tg?.initData || "", booking_id: bookingId, action }),
    });
    const d = await r.json();
    if (r.ok) {
      const toastMsg = action === "confirm" ? t("action_confirm_ok")
                     : action === "en_route" ? "🟠 " + t("status_en_route")
                     : action === "arrived" ? "✅ " + t("status_confirmed")
                     : t("action_reject_ok");
      toast(toastMsg);
      haptic("notify", (action === "confirm" || action === "arrived") ? "success" : action === "en_route" ? "warning" : "error");
      // Immediately refresh ALL live views so everything stays in sync
      if (state.step === 0 || state.step === 1) loadFloorPlan();
      loadLiveFloor();
      loadStaffPanel();
    } else {
      toast(d.detail || "Ошибка", true);
    }
  } catch {
    toast("Нет соединения", true);
  }
}

function startStaffRefresh() {
  stopStaffRefresh();
  staffTimer = setInterval(() => {
    if (staffView.style.display !== "none") loadStaffPanel();
  }, 15_000);
}
function stopStaffRefresh() {
  if (staffTimer) { clearInterval(staffTimer); staffTimer = null; }
}

/* ─────────── LIVE TABLES TAB ─────────── */
let liveHall       = "main";
let tablesTimer    = null;

// Hall switcher inside tables view
document.getElementById("tables-hall-tabs").addEventListener("click", e => {
  const btn = e.target.closest(".seg-btn");
  if (!btn) return;
  liveHall = btn.dataset.lhall;
  document.querySelectorAll("#tables-hall-tabs .seg-btn").forEach(b =>
    b.classList.toggle("active", b === btn));
  haptic("sel");
  loadLiveFloor();
});
document.getElementById("tables-refresh").addEventListener("click", () => {
  loadLiveFloor(); haptic("impact", "light");
});

async function loadLiveFloor() {
  const now   = new Date();
  const date  = getVNDateISO();
  const vnStr = now.toLocaleTimeString("en-GB", { timeZone: "Asia/Ho_Chi_Minh", hour: "2-digit", minute: "2-digit" });
  const [hh, mm] = vnStr.split(":").map(Number);

  const sub = document.getElementById("tables-updated");
  if (sub) sub.textContent = t("live_updated", String(hh).padStart(2,"0"), String(mm).padStart(2,"0"));

  const botLabel = document.getElementById("tables-label-bot");
  if (botLabel) botLabel.style.display = liveHall === "main" ? "" : "none";

  // Convert VN time to minutes; 00-02h treated as 24-26h (overnight slots)
  const adjH = hh <= 2 ? hh + 24 : hh;
  const currentMinutes = adjH * 60 + mm;

  try {
    const r = await fetchT(`/api/tables/live?hall=${liveHall}&date=${date}&current_minutes=${currentMinutes}`);
    const d = await r.json();
    renderLiveFloor(d.tables || {});
  } catch {
    renderLiveFloor({});
  }
}

function renderLiveFloor(tables) {
  _liveFloorCache = { tables };
  stopLiveCountdown();
  const layout = LAYOUTS[liveHall];
  const fp     = document.getElementById("tables-floor");

  fp.className = "floor-map";
  fp.removeAttribute("style");
  fp.innerHTML = "";

  // Background SVG
  const bg = document.createElement("img");
  bg.src       = layout.img + "?v=9";
  bg.alt       = layout.hallLabel;
  bg.draggable = false;
  bg.className = "floor-map-bg";
  fp.appendChild(bg);

  // Section labels
  if (layout.sectionLabels) {
    layout.sectionLabels.forEach(sec => {
      const lbl = document.createElement("div");
      lbl.className = "floor-section-lbl" + (sec.vertical ? " floor-section-lbl--vertical" : "");
      lbl.style.left = sec.x + "%";
      lbl.style.top  = sec.y + "%";
      lbl.textContent = t(sec.key);
      fp.appendChild(lbl);
    });
  }

  const STATUS_CLASS = { free: "free", pending: "pending", en_route: "en_route", confirmed: "busy" };
  const LABEL        = { free: t("live_slabel_free"), pending: t("live_slabel_pend"), en_route: t("live_slabel_enroute"), busy: t("live_slabel_busy") };

  let hasOccupied = false;

  Object.entries(layout.tables).forEach(([cellId, pos]) => {
    {
      const fakeCell = cellId;

      // New format: tables[cellId] = {status, remaining_min}
      const rawObj    = tables[cellId] || { status: "free", remaining_min: 0 };
      const rawStatus = rawObj.status || "free";
      const remainMin = rawObj.remaining_min || 0;

      const cls  = STATUS_CLASS[rawStatus] || "free";
      const info = TABLE_INFO[cellId];
      const el   = document.createElement("div");
      el.className = `tbl tbl-pin tbl-live ${cls}`;
      if (pos.shape === "circle") el.classList.add("tbl-pin-circle");
      el.style.left = pos.x + "%";
      el.style.top  = pos.y + "%";
      if (pos.shape === "circle") {
        el.style.width       = "12%";
        el.style.aspectRatio = "1";
      } else {
        if (pos.w) el.style.width  = pos.w + "%";
        if (pos.h) el.style.height = pos.h + "%";
      }
      el.style.pointerEvents = "auto";
      if (info?.deposit > 0) el.classList.add("tbl-has-dep");

      const numSpan = document.createElement("span");
      numSpan.className = "tbl-num";
      numSpan.textContent = cellId;
      el.appendChild(numSpan);

      if (info) {
        const capSpan = document.createElement("span");
        capSpan.className = "tbl-cap";
        capSpan.textContent = info.cap === 1 ? t("cap_one") : t("cap_many", info.cap);
        el.appendChild(capSpan);
      }

      // Status label — always visible
      const stSpan = document.createElement("span");
      stSpan.className = "tbl-status";
      if (pos.shape === "circle") {
        const STATUS_ICON = { free: "✓", pending: "●", en_route: "◔", busy: "✕" };
        stSpan.textContent = STATUS_ICON[cls] || "✓";
      } else {
        stSpan.textContent = LABEL[cls] || t("live_slabel_free");
      }
      el.appendChild(stSpan);

      // Remaining time countdown (only for occupied tables with active booking)
      if (rawStatus !== "free" && remainMin > 0) {
        hasOccupied = true;
        const remainSec = remainMin * 60;
        const remSpan = document.createElement("span");
        remSpan.className = "tbl-remain" + (remainMin <= 10 ? " tbl-remain-red" : remainMin <= 30 ? " tbl-remain-amber" : "");
        remSpan.dataset.remainSec = remainSec;
        remSpan.textContent = _fmtRemain(remainSec);
        el.appendChild(remSpan);
      } else if (rawStatus === "pending" && remainMin === 0) {
        // Upcoming pending booking — show "скоро" label instead of countdown
        const upSpan = document.createElement("span");
        upSpan.className = "tbl-remain";
        upSpan.style.color = "#e9d5ff";
        upSpan.textContent = t("live_soon");
        el.appendChild(upSpan);
      }

      if (info?.deposit > 0) {
        const dot = document.createElement("span");
        dot.className = "tbl-dep-dot";
        dot.title = t("deposit_title");
        el.appendChild(dot);
      }

      if (rawObj.is_vip && rawStatus !== "free") {
        const vipBadge = document.createElement("span");
        vipBadge.className = "tbl-vip-crown";
        vipBadge.textContent = "👑";
        el.appendChild(vipBadge);
      }

      el.title = `${t("table_prefix")} ${cellId} — ${LABEL[cls] || cls}`;
      el.style.cursor = "pointer";
      el.addEventListener("click", () => {
        haptic("impact", "light");
        showTableSheet(cellId, rawStatus, remainMin);
      });
      fp.appendChild(el);
    }
  });

  if (hasOccupied) {
    startLiveCountdown();
  }
}

function startTablesRefresh() {
  stopTablesRefresh();
  tablesTimer = setInterval(() => {
    if (tablesView && tablesView.style.display !== "none") loadLiveFloor();
  }, 30_000);
}
function stopTablesRefresh() {
  if (tablesTimer) { clearInterval(tablesTimer); tablesTimer = null; }
}

/* ── Live table remaining-time countdown ── */
let _liveCountTimer = null;
function _fmtRemain(sec) {
  if (sec <= 0) return "—";
  const totalMin = Math.floor(sec / 60);
  const s = sec % 60;
  if (totalMin >= 60) {
    const h = Math.floor(totalMin / 60);
    const m = totalMin % 60;
    return `${h}ч ${String(m).padStart(2,"0")}м`;
  }
  return `${totalMin}:${String(s).padStart(2, "0")}`;
}
function startLiveCountdown() {
  stopLiveCountdown();
  _liveCountTimer = setInterval(_tickLiveTables, 1000);
}
function stopLiveCountdown() {
  if (_liveCountTimer) { clearInterval(_liveCountTimer); _liveCountTimer = null; }
}
function _tickLiveTables() {
  const els = document.querySelectorAll(".tbl-remain[data-remain-sec]");
  if (!els.length) { stopLiveCountdown(); return; }
  let anyExpired = false;
  els.forEach(el => {
    let sec = parseInt(el.dataset.remainSec) - 1;
    if (sec < 0) sec = 0;
    el.dataset.remainSec = sec;
    el.textContent = _fmtRemain(sec);
    if      (sec <= 600)  el.className = "tbl-remain tbl-remain-red";
    else if (sec <= 1800) el.className = "tbl-remain tbl-remain-amber";
    else                  el.className = "tbl-remain";
    if (sec === 0) anyExpired = true;
  });
  if (anyExpired) {
    stopLiveCountdown();
    setTimeout(() => loadLiveFloor(), 2000);
  }
}

/* ─────────── REGULARS (GUEST PROFILES) ─────────── */

let _regularsData   = [];   // cached full list from server
let _regularsFilter = "all"; // "all" | "vip"

// ── Language-rehydration caches ──
let _staffBookingsCache = null; // { bookings[], filter } — last loaded staff list
let _occupiedItemsCache = null; // [] — last loaded occupied tables
let _liveFloorCache     = null; // { tables } — last live floor data

async function loadRegulars(q = "") {
  const listEl  = document.getElementById("regulars-list");
  const countEl = document.getElementById("regulars-count");
  if (!listEl) return;
  listEl.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("loading")}</div>`;
  const initData = tg?.initData || "";
  try {
    const url = `/api/staff/guests?q=${encodeURIComponent(q)}&init_data=${encodeURIComponent(initData)}`;
    const r   = await fetchT(url);
    const d   = await r.json();
    _regularsData = d.guests || [];
    _applyRegularsFilter();
  } catch {
    listEl.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("error_load")}</div>`;
  }
}

function _applyRegularsFilter() {
  const countEl = document.getElementById("regulars-count");
  const filtered = _regularsFilter === "vip"
    ? _regularsData.filter(g => g.is_vip)
    : _regularsData;
  if (countEl) countEl.textContent = t("reg_count", filtered.length);
  renderRegulars(filtered);
}

function renderRegulars(guests) {
  const listEl = document.getElementById("regulars-list");
  if (!listEl) return;
  if (guests.length === 0) {
    listEl.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("reg_empty")}</div>`;
    return;
  }
  listEl.innerHTML = "";
  guests.forEach(g => {
    const card = document.createElement("div");
    card.className = "reg-card";
    card.innerHTML = `
      <div class="reg-card-top">
        <span class="reg-card-name">${g.name}</span>
        ${g.is_vip ? '<span class="reg-vip-badge">⭐ VIP</span>' : ''}
      </div>
      <div class="reg-card-meta">📞 ${g.phone} &nbsp;·&nbsp; 🕒 ${t("reg_visits", g.total_visits)}</div>
      ${g.notes ? `<div class="reg-card-notes">"​${g.notes}"</div>` : ''}
      <div class="reg-card-actions">
        <button class="reg-btn reg-btn-book" onclick="bookFromGuest('${esc(g.name)}','${esc(g.phone)}')">${t("reg_btn_book")}</button>
        <button class="reg-btn reg-btn-vip" onclick="toggleVip('${esc(g.phone)}',${g.is_vip})">${g.is_vip ? t("reg_btn_vip_off") : t("reg_btn_vip_on")}</button>
        <button class="reg-btn reg-btn-notes" onclick="editGuestNotes('${esc(g.phone)}','${esc(g.notes || '')}')">${t("reg_btn_note")}</button>
      </div>
    `;
    listEl.appendChild(card);
  });
}

// Filter tab buttons
document.getElementById("reg-filter-all")?.addEventListener("click", () => {
  _regularsFilter = "all";
  document.getElementById("reg-filter-all")?.classList.add("active");
  document.getElementById("reg-filter-vip")?.classList.remove("active");
  _applyRegularsFilter();
  haptic("sel");
});
document.getElementById("reg-filter-vip")?.addEventListener("click", () => {
  _regularsFilter = "vip";
  document.getElementById("reg-filter-vip")?.classList.add("active");
  document.getElementById("reg-filter-all")?.classList.remove("active");
  _applyRegularsFilter();
  haptic("sel");
});

// Add guest button
document.getElementById("regulars-add")?.addEventListener("click", () => showAddGuestModal());

function showAddGuestModal() {
  const overlay = document.createElement("div");
  overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;display:flex;align-items:flex-end;justify-content:center";
  overlay.innerHTML = `
    <div style="width:100%;max-width:480px;background:#0d1220;border-radius:20px 20px 0 0;padding:24px 20px 36px">
      <div style="font-weight:700;font-size:17px;margin-bottom:18px">${t("add_guest_title")}</div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:10px 14px;display:flex;gap:10px;align-items:center">
          <span>📞</span>
          <input id="_ag-phone" type="tel" placeholder="${t('add_guest_phone_ph')}" style="flex:1;background:none;border:none;outline:none;color:#e8eaf5;font-size:14px" autocomplete="tel"/>
        </div>
        <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:10px 14px;display:flex;gap:10px;align-items:center">
          <span>👤</span>
          <input id="_ag-name" type="text" placeholder="${t('add_guest_name_ph')}" style="flex:1;background:none;border:none;outline:none;color:#e8eaf5;font-size:14px" autocomplete="name"/>
        </div>
        <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:10px 14px;display:flex;gap:10px;align-items:flex-start">
          <span>📝</span>
          <textarea id="_ag-notes" rows="2" placeholder="${t('add_guest_notes_ph')}" style="flex:1;background:none;border:none;outline:none;color:#e8eaf5;font-size:14px;resize:none"></textarea>
        </div>
        <label style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.25);border-radius:10px;cursor:pointer">
          <input id="_ag-vip" type="checkbox" style="width:18px;height:18px;accent-color:#f59e0b"/>
          <span style="font-size:14px;color:#fbbf24;font-weight:600">${t("add_guest_vip_lbl")}</span>
        </label>
      </div>
      <div style="display:flex;gap:10px;margin-top:18px">
        <button id="_ag-save" style="flex:1;padding:13px;border-radius:12px;border:none;background:var(--c-accent);color:#fff;font-weight:700;font-size:15px;cursor:pointer">${t("add_guest_save")}</button>
        <button id="_ag-cancel" style="flex:1;padding:13px;border-radius:12px;border:none;background:rgba(255,255,255,.1);color:#aaa;font-size:14px;cursor:pointer">${t("add_guest_cancel")}</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  const close = () => document.body.removeChild(overlay);
  overlay.querySelector("#_ag-cancel").onclick = close;
  overlay.querySelector("#_ag-save").onclick = async () => {
    const phone  = overlay.querySelector("#_ag-phone").value.trim();
    const name   = overlay.querySelector("#_ag-name").value.trim();
    const notes  = overlay.querySelector("#_ag-notes").value.trim();
    const is_vip = overlay.querySelector("#_ag-vip").checked;
    if (!phone) { toast(t("add_guest_no_phone"), true); return; }
    if (!name)  { toast(t("add_guest_no_name"), true); return; }
    const initData = tg?.initData || "";
    try {
      const r = await fetchT("/api/staff/guest/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ init_data: initData, phone, name, notes, is_vip }),
      });
      const d = await r.json();
      if (d.ok) {
        toast(t("add_guest_ok", name));
        close();
        loadRegulars(document.getElementById("regulars-search")?.value.trim() || "");
      } else { toast(t("add_guest_err"), true); }
    } catch { toast(t("err_conn"), true); }
  };
}

function esc(str) {
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function bookFromGuest(name, phone) {
  state.prefilledGuest = { name, phone };
  haptic("impact");
  setActiveTab(tabBook);
  showView(bookView);
  stopStaffRefresh(); stopTablesRefresh(); stopCountdown(); stopLiveCountdown();
  // Reset to step 0 (floor plan) so admin picks table
  state.table = ""; state.date = ""; state.time = "";
  goTo(0);
  startRefresh();
  toast(`📅 Бронь для ${name}`);
}

async function toggleVip(phone, isVip) {
  const newVip = !isVip;
  const initData = tg?.initData || "";
  try {
    await fetchT("/api/staff/guest/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: initData, phone, is_vip: newVip }),
    });
    toast(newVip ? t("reg_vip_on") : t("reg_vip_off"));
    loadRegulars(document.getElementById("regulars-search")?.value.trim() || "");
  } catch {
    toast(t("err_conn"), true);
  }
}

async function editGuestNotes(phone, currentNotes) {
  const newNotes = await new Promise(resolve => {
    // Build a simple inline edit overlay
    const overlay = document.createElement("div");
    overlay.style.cssText = `position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;display:flex;align-items:flex-end;justify-content:center`;
    overlay.innerHTML = `
      <div style="width:100%;max-width:480px;background:#0d1220;border-radius:20px 20px 0 0;padding:24px 20px 32px">
        <div style="font-weight:700;font-size:16px;margin-bottom:14px">${t("notes_title")}</div>
        <textarea id="_notes-ta" rows="3" style="width:100%;box-sizing:border-box;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:10px 12px;color:#e8eaf5;font-size:14px;resize:none;outline:none">${currentNotes}</textarea>
        <div style="display:flex;gap:10px;margin-top:14px">
          <button id="_notes-save" style="flex:1;padding:12px;border-radius:10px;border:none;background:var(--c-accent);color:#fff;font-weight:700;font-size:14px;cursor:pointer">${t("notes_save")}</button>
          <button id="_notes-cancel" style="flex:1;padding:12px;border-radius:10px;border:none;background:rgba(255,255,255,.1);color:#aaa;font-size:14px;cursor:pointer">${t("notes_cancel")}</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    overlay.querySelector("#_notes-save").onclick = () => { document.body.removeChild(overlay); resolve(overlay.querySelector("#_notes-ta").value.trim()); };
    overlay.querySelector("#_notes-cancel").onclick = () => { document.body.removeChild(overlay); resolve(null); };
  });
  if (newNotes === null) return;
  const initData = tg?.initData || "";
  try {
    await fetchT("/api/staff/guest/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: initData, phone, notes: newNotes }),
    });
    toast(t("notes_ok"));
    loadRegulars(document.getElementById("regulars-search")?.value.trim() || "");
  } catch {
    toast(t("err_conn"), true);
  }
}

// Search input — debounced
let _regSearchTimer = null;
document.getElementById("regulars-search")?.addEventListener("input", e => {
  clearTimeout(_regSearchTimer);
  _regSearchTimer = setTimeout(() => loadRegulars(e.target.value.trim()), 300);
});

document.getElementById("regulars-refresh")?.addEventListener("click", () => {
  const activePanel = document.getElementById("reg-panel-blacklist")?.style.display !== "none";
  if (activePanel) {
    loadBlacklist(document.getElementById("blacklist-search")?.value.trim() || "");
  } else {
    loadRegulars(document.getElementById("regulars-search")?.value.trim() || "");
  }
  haptic("impact", "light");
});

/* ─────────── SUBTABS: GUESTS / BLACKLIST ─────────── */

document.getElementById("reg-subtab-guests")?.addEventListener("click", () => {
  document.getElementById("reg-panel-guests").style.display = "";
  document.getElementById("reg-panel-blacklist").style.display = "none";
  document.getElementById("reg-subtab-guests")?.classList.add("active");
  document.getElementById("reg-subtab-blacklist")?.classList.remove("active");
  document.getElementById("regulars-add").style.display = "";
  haptic("sel");
});

document.getElementById("reg-subtab-blacklist")?.addEventListener("click", () => {
  document.getElementById("reg-panel-guests").style.display = "none";
  document.getElementById("reg-panel-blacklist").style.display = "";
  document.getElementById("reg-subtab-blacklist")?.classList.add("active");
  document.getElementById("reg-subtab-guests")?.classList.remove("active");
  document.getElementById("regulars-add").style.display = "none";
  haptic("sel");
  loadBlacklist();
});

/* ─────────── BLACKLIST ─────────── */

let _blacklistData   = [];
let _blacklistTimer  = null;

async function loadBlacklist(q = "") {
  const listEl = document.getElementById("blacklist-list");
  if (!listEl) return;
  listEl.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("loading")}</div>`;
  const initData = tg?.initData || "";
  try {
    const url = `/api/staff/blacklist?q=${encodeURIComponent(q)}&init_data=${encodeURIComponent(initData)}`;
    const r = await fetchT(url);
    const d = await r.json();
    _blacklistData = d.blacklist || [];
    renderBlacklist(_blacklistData);
  } catch {
    listEl.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("error_load")}</div>`;
  }
}

function renderBlacklist(entries) {
  const listEl = document.getElementById("blacklist-list");
  if (!listEl) return;
  if (entries.length === 0) {
    listEl.innerHTML = `<div class="muted-text" style="text-align:center;padding:40px 0">${t("bl_empty")}</div>`;
    return;
  }
  listEl.innerHTML = "";
  entries.forEach(e => {
    const card = document.createElement("div");
    card.className = "reg-card";
    card.style.borderLeft = "3px solid #ef4444";
    const nameLine = e.name ? `<span class="reg-card-name" style="color:#fca5a5">${e.name}</span>` : '<span class="reg-card-name" style="color:#fca5a5">—</span>';
    const phoneLine = e.phone ? `📞 ${e.phone}` : "";
    const tgLine = e.tg_username ? `✈️ @${e.tg_username}` : "";
    const reasonLine = e.reason ? `<div class="reg-card-notes" style="color:#fca5a5">🚫 ${e.reason}</div>` : "";
    const dateLine = e.created_at ? `<span style="font-size:11px;color:var(--c-sub)">${t("bl_date_lbl")} ${e.created_at}</span>` : "";
    const meta = [phoneLine, tgLine].filter(Boolean).join(" &nbsp;·&nbsp; ");
    card.innerHTML = `
      <div class="reg-card-top">
        ${nameLine}
        <span style="background:#7f1d1d;color:#fca5a5;padding:2px 7px;border-radius:8px;font-size:11px;font-weight:700">🚫 БЛОК</span>
      </div>
      ${meta ? `<div class="reg-card-meta">${meta}</div>` : ""}
      ${reasonLine}
      ${dateLine}
      <div class="reg-card-actions" style="margin-top:8px">
        <button class="reg-btn" style="background:rgba(239,68,68,.15);color:#fca5a5;border-color:rgba(239,68,68,.3)" onclick="removeFromBlacklist(${e.id},'${esc(e.name || e.phone || e.tg_username || '')}')">${t("bl_remove_ok")}</button>
      </div>
    `;
    listEl.appendChild(card);
  });
}

async function removeFromBlacklist(id, displayName) {
  if (!confirm(`${t("bl_remove_confirm")} (${displayName})`)) return;
  const initData = tg?.initData || "";
  try {
    const r = await fetchT("/api/staff/blacklist/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: initData, id }),
    });
    const d = await r.json();
    if (d.ok) {
      toast(t("bl_remove_ok"));
      loadBlacklist(document.getElementById("blacklist-search")?.value.trim() || "");
    } else {
      toast(t("bl_remove_err"), true);
    }
  } catch {
    toast(t("err_conn"), true);
  }
}

function showAddBlacklistModal() {
  const overlay = document.createElement("div");
  overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;display:flex;align-items:flex-end;justify-content:center";
  overlay.innerHTML = `
    <div style="width:100%;max-width:480px;background:#0d1220;border-radius:20px 20px 0 0;padding:24px 20px 36px">
      <div style="font-weight:700;font-size:17px;margin-bottom:18px;color:#fca5a5">${t("bl_add_title")}</div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:10px;padding:10px 14px;display:flex;gap:10px;align-items:center">
          <span>📞</span>
          <input id="_bl-phone" type="tel" placeholder="${t('bl_add_phone_ph')}" style="flex:1;background:none;border:none;outline:none;color:#e8eaf5;font-size:14px" autocomplete="tel"/>
        </div>
        <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:10px;padding:10px 14px;display:flex;gap:10px;align-items:center">
          <span>✈️</span>
          <input id="_bl-tg" type="text" placeholder="${t('bl_add_tg_ph')}" style="flex:1;background:none;border:none;outline:none;color:#e8eaf5;font-size:14px" autocomplete="off"/>
        </div>
        <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:10px;padding:10px 14px;display:flex;gap:10px;align-items:center">
          <span>👤</span>
          <input id="_bl-name" type="text" placeholder="${t('bl_add_name_ph')}" style="flex:1;background:none;border:none;outline:none;color:#e8eaf5;font-size:14px" autocomplete="name"/>
        </div>
        <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:10px;padding:10px 14px;display:flex;gap:10px;align-items:flex-start">
          <span>🚫</span>
          <textarea id="_bl-reason" rows="2" placeholder="${t('bl_add_reason_ph')}" style="flex:1;background:none;border:none;outline:none;color:#e8eaf5;font-size:14px;resize:none"></textarea>
        </div>
      </div>
      <div style="display:flex;gap:10px;margin-top:18px">
        <button id="_bl-save" style="flex:1;padding:13px;border-radius:12px;border:none;background:#ef4444;color:#fff;font-weight:700;font-size:15px;cursor:pointer">${t("bl_add_save")}</button>
        <button id="_bl-cancel" style="flex:1;padding:13px;border-radius:12px;border:none;background:rgba(255,255,255,.1);color:#aaa;font-size:14px;cursor:pointer">${t("bl_add_cancel")}</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  const close = () => document.body.removeChild(overlay);
  overlay.querySelector("#_bl-cancel").onclick = close;
  overlay.querySelector("#_bl-save").onclick = async () => {
    const phone  = overlay.querySelector("#_bl-phone").value.trim();
    const tgUser = overlay.querySelector("#_bl-tg").value.trim().replace(/^@/, "");
    const name   = overlay.querySelector("#_bl-name").value.trim();
    const reason = overlay.querySelector("#_bl-reason").value.trim();
    if (!phone && !tgUser) { toast(t("bl_add_no_id"), true); return; }
    const initData = tg?.initData || "";
    try {
      const r = await fetchT("/api/staff/blacklist/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ init_data: initData, phone, tg_username: tgUser, name, reason }),
      });
      const d = await r.json();
      if (d.ok) {
        toast(t("bl_add_ok", name));
        close();
        loadBlacklist(document.getElementById("blacklist-search")?.value.trim() || "");
      } else { toast(t("bl_add_err"), true); }
    } catch { toast(t("err_conn"), true); }
  };
}

document.getElementById("blacklist-add-btn")?.addEventListener("click", () => showAddBlacklistModal());

// Blacklist search — debounced
document.getElementById("blacklist-search")?.addEventListener("input", e => {
  clearTimeout(_blacklistTimer);
  _blacklistTimer = setTimeout(() => loadBlacklist(e.target.value.trim()), 300);
});

/* ─────────── VIETNAM CLOCK + HAPPY HOURS ─────────── */
function tickVNClock() {
  try {
    const now = new Date();
    const t   = now.toLocaleTimeString("en-GB", { timeZone: "Asia/Ho_Chi_Minh", hour: "2-digit", minute: "2-digit" });
    const el  = document.getElementById("vn-time");
    if (el) el.textContent = t;

    const h = parseInt(t.split(":")[0], 10);
    const banner = document.getElementById("happy-banner");
    if (banner) banner.style.display = (h >= 12 && h < 16) ? "" : "none";
  } catch { /* ignore */ }
}
tickVNClock();
setInterval(tickVNClock, 30_000);

/* ─────────── EXTERNAL LINKS (location + menu) ─────────── */
function openExternal(url) {
  if (tg?.openLink) {
    tg.openLink(url, { try_instant_view: false });
  } else {
    window.open(url, "_blank", "noopener");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const viLoc = document.getElementById("vi-location");
  if (viLoc) {
    viLoc.addEventListener("click", (e) => {
      e.preventDefault();
      openExternal(viLoc.href);
      haptic("impact", "light");
    });
  }
  document.querySelectorAll(".menu-big-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      openExternal(btn.href);
      haptic("impact", "medium");
    });
  });
});

/* ─────────── INIT ─────────── */
(async () => {
  await detectStaff();
  goTo(0);
})();
