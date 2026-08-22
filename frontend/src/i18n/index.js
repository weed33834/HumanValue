import { createI18n } from 'vue-i18n'
import en from './locales/en'
import zh from './locales/zh'
import ja from './locales/ja'

// 默认英文 (对外宣传以英文为主), 可切换 中文/日文
const LOCALE_KEY = 'humanvalue_locale'
const SUPPORTED = ['en', 'zh', 'ja']

function initialLocale() {
  try {
    const saved = localStorage.getItem(LOCALE_KEY)
    if (saved && SUPPORTED.includes(saved)) return saved
    // 跟随浏览器语言, 中文系→zh, 日文→ja, 其余→en
    const nav = (navigator.language || 'en').toLowerCase()
    if (nav.startsWith('zh')) return 'zh'
    if (nav.startsWith('ja')) return 'ja'
    return 'en'
  } catch {
    return 'en'
  }
}

const i18n = createI18n({
  legacy: false, // composition API
  globalInjection: true,
  locale: initialLocale(),
  fallbackLocale: 'en',
  messages: { en, zh, ja },
})

export function setLocale(locale) {
  if (!SUPPORTED.includes(locale)) locale = 'en'
  i18n.global.locale.value = locale
  try {
    localStorage.setItem(LOCALE_KEY, locale)
    document.documentElement.lang = locale
  } catch {
    // ignore storage/DOM errors
  }
  return locale
}

export function getLocale() {
  return i18n.global.locale.value
}

export const SUPPORTED_LOCALES = SUPPORTED

export default i18n
