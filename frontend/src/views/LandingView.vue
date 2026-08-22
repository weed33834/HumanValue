<template>
  <div class="landing">
    <!-- 顶部导航 -->
    <header class="landing-nav">
      <BrandLogo :size="34" :text-size="19" wordmark="HumanValue" show-tag />
      <nav class="landing-nav__links" aria-:label="$t('v.LandingView.0')">
        <a href="#features">{ $t('v.LandingView.15') }</a>
        <a href="#cases">{ $t('v.LandingView.14') }</a>
        <a href="#about">{ $t('v.LandingView.17') }</a>
      </nav>
      <div class="landing-nav__actions">
        <el-button text class="nav-btn" @click="goLogin">{ $t('v.LandingView.16') }</el-button>
        <el-button type="primary" round class="nav-btn" @click="goRegister"
          >{ $t('v.LandingView.10') }</el-button
        >
      </div>
    </header>

    <!-- 主视觉区 -->
    <section class="landing-hero">
      <div class="hero-bg" aria-hidden="true"></div>
      <div class="hero-content">
        <div class="hero-badge">{ $t('v.LandingView.3') }</div>
        <h1 class="hero-title">
          让每一次人才评估
          <span class="gradient-text">{ $t('v.LandingView.12') }</span>
        </h1>
        <p class="hero-sub">
          HumanValue 以 Agent 为核心，融合多维度数据与真实 LLM，
          为团队提供精准、可追溯、可行动的人才评估与成长指引。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" round class="cta-primary" @click="goRegister">
            免费注册
          </el-button>
          <el-button size="large" round class="cta-secondary" @click="guestLogin">
            游客体验
          </el-button>
        </div>
        <div class="hero-meta">
          <span>{ $t('v.LandingView.8') }</span>
          <span class="dot">·</span>
          <span>{ $t('v.LandingView.6') }</span>
          <span class="dot">·</span>
          <span>{ $t('v.LandingView.5') }</span>
        </div>
      </div>
    </section>

    <!-- 特性区 -->
    <section id="features" class="landing-section">
      <h2 class="section-title">{ $t('v.LandingView.13') }</h2>
      <div class="feature-grid">
        <div v-for="f in features" :key="f.title" class="feature-card av-rise">
          <div class="feature-icon" :aria-hidden="true">{{ f.icon }}</div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <!-- 案例区 -->
    <section id="cases" class="landing-section landing-section--alt">
      <h2 class="section-title">{ $t('v.LandingView.7') }</h2>
      <div class="case-grid">
        <a
          v-for="c in cases"
          :key="c.name"
          class="case-card av-rise"
          :href="c.link"
          target="_blank"
        >
          <div class="case-score" :class="scoreClass(c.score)">{{ c.score }}</div>
          <h4>{{ c.name }}</h4>
          <p>{{ c.desc }}</p>
        </a>
      </div>
    </section>

    <!-- 关于/页脚 -->
    <section id="about" class="landing-footer">
      <BrandLogo :size="28" :text-size="16" wordmark="HumanValue" />
      <p>{ $t('v.LandingView.2') }</p>
      <div class="footer-links">
        <a href="https://github.com/weed33834" target="_blank" rel="noopener">GitHub</a>
        <span class="dot">·</span>
        <a href="https://gitcode.com/badhope" target="_blank" rel="noopener">GitCode</a>
        <span class="dot">·</span>
        <a href="https://gitee.com/badhope" target="_blank" rel="noopener">Gitee</a>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import BrandLogo from '@/components/BrandLogo.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

onMounted(() => {
  if (auth.isLoggedIn) {
    router.replace('/boss')
  }
})

const features = [
  { icon: 'A', title: 'Agent 智能评估', desc: '以 Agent 为核心，多工具协作，产出可追溯的深度评估' },
  { icon: 'G', title: '风险自动预警', desc: '低分与高风险自动路由 HR，规避决策盲区' },
  { icon: 'C', title: '对话式分析', desc: '想问谁问谁，用自然语言洞察团队与人才' },
  { icon: 'K', title: '知识库融合', desc: '接入企业知识库，让评估贴合业务语境' },
  { icon: 'M', title: '全端覆盖', desc: '桌面 + 移动端，随时随地掌握人才动态' },
  { icon: 'S', title: '安全合规', desc: '审计留痕、脱敏护栏、多租户隔离' },
]

const cases = [
  {
    name: '腾讯人才评估',
    score: '88.75',
    desc: '识别优势与成长瓶颈，指引 Owner 转型',
    link: 'docs/demo/cases.md',
  },
  {
    name: '恒大危机复盘',
    score: '32.5',
    desc: 'critical 风险自动路由 HR，处置建议落地',
    link: 'docs/demo/cases.md',
  },
  {
    name: '清华学者评估',
    score: '82.5',
    desc: '科研人才画像，勾勒独立 PI 成长路径',
    link: 'docs/demo/cases.md',
  },
  {
    name: '斯坦福诺奖学者',
    score: '94.2',
    desc: '识别顶尖人才的高端瓶颈与突破方向',
    link: 'docs/demo/cases.md',
  },
]

function scoreClass(score) {
  const s = parseFloat(score)
  if (s >= 85) return 'score--high'
  if (s >= 60) return 'score--mid'
  return 'score--low'
}

function goLogin() {
  router.push('/login')
}

function goRegister() {
  router.push('/login?register=1')
}

function guestLogin() {
  try {
    auth.loginDemo('boss')
    router.push('/boss')
  } catch {
    ElMessage.error('游客模式不可用')
  }
}
</script>

<style scoped>
.landing {
  min-height: 100vh;
  background: linear-gradient(180deg, #0b1026 0%, #0d1330 50%, #0b1026 100%);
  color: #f5e6c8;
  overflow-x: hidden;
}
.landing-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 48px;
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(11, 16, 38, 0.7);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(201, 168, 106, 0.12);
}
.landing-nav__links {
  display: flex;
  gap: 28px;
}
.landing-nav__links a {
  color: #8b92a8;
  text-decoration: none;
  font-size: 14px;
  letter-spacing: 0.5px;
  transition: color 0.25s;
}
.landing-nav__links a:hover {
  color: #c9a86a;
}
.landing-nav__actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
.nav-btn {
  color: #c9a86a;
}

.landing-hero {
  position: relative;
  padding: 72px 48px 96px;
  text-align: center;
}
.hero-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 600px 300px at 30% 20%, rgba(79, 124, 255, 0.12), transparent),
    radial-gradient(ellipse 600px 300px at 70% 30%, rgba(124, 92, 255, 0.1), transparent);
}
.hero-content {
  position: relative;
  max-width: 760px;
  margin: 0 auto;
}
.hero-badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 999px;
  border: 1px solid rgba(201, 168, 106, 0.35);
  color: #c9a86a;
  font-size: 13px;
  letter-spacing: 1px;
  margin-bottom: 24px;
}
.hero-title {
  font-size: 52px;
  font-weight: 700;
  line-height: 1.15;
  margin: 0 0 20px;
  letter-spacing: 1px;
}
.gradient-text {
  background: linear-gradient(90deg, #4f7cff, #7c5cff, #b44cff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.hero-sub {
  font-size: 17px;
  line-height: 1.8;
  color: #8b92a8;
  max-width: 600px;
  margin: 0 auto 36px;
}
.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 24px;
}
.cta-primary {
  padding: 12px 40px;
  font-size: 16px;
}
.cta-secondary {
  padding: 12px 40px;
  font-size: 16px;
  border-color: rgba(201, 168, 106, 0.5);
  color: #c9a86a;
}
.hero-meta {
  color: #5a6280;
  font-size: 13px;
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
}
.dot {
  opacity: 0.5;
}

.landing-section {
  padding: 72px 48px;
}
.landing-section--alt {
  background: rgba(255, 255, 255, 0.02);
}
.section-title {
  text-align: center;
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 48px;
  letter-spacing: 2px;
  color: #f5e6c8;
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  max-width: 1080px;
  margin: 0 auto;
}
.feature-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(201, 168, 106, 0.15);
  border-radius: 16px;
  padding: 28px;
  transition:
    transform 0.3s,
    border-color 0.3s,
    box-shadow 0.3s;
}
.feature-card:hover {
  transform: translateY(-4px);
  border-color: rgba(201, 168, 106, 0.4);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
}
.feature-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #4f7cff, #7c5cff);
  margin-bottom: 16px;
}
.feature-card h3 {
  font-size: 17px;
  margin: 0 0 8px;
}
.feature-card p {
  font-size: 14px;
  color: #8b92a8;
  line-height: 1.6;
  margin: 0;
}

.case-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  max-width: 1080px;
  margin: 0 auto;
}
.case-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(201, 168, 106, 0.15);
  border-radius: 16px;
  padding: 24px;
  text-decoration: none;
  color: inherit;
  transition:
    transform 0.3s,
    border-color 0.3s;
}
.case-card:hover {
  transform: translateY(-4px);
  border-color: rgba(201, 168, 106, 0.4);
}
.case-score {
  display: inline-block;
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
}
.score--high {
  color: #4ade80;
}
.score--mid {
  color: #fbbf24;
}
.score--low {
  color: #f87171;
}
.case-card h4 {
  font-size: 16px;
  margin: 0 0 8px;
}
.case-card p {
  font-size: 13px;
  color: #8b92a8;
  line-height: 1.5;
  margin: 0;
}

.landing-footer {
  text-align: center;
  padding: 48px;
  border-top: 1px solid rgba(201, 168, 106, 0.1);
}
.landing-footer p {
  color: #8b92a8;
  font-size: 14px;
  margin: 12px 0;
}
.footer-links {
  display: flex;
  gap: 8px;
  justify-content: center;
  color: #5a6280;
  font-size: 13px;
}
.footer-links a {
  color: #8b92a8;
  text-decoration: none;
}
.footer-links a:hover {
  color: #c9a86a;
}

@media (max-width: 768px) {
  .landing-nav {
    padding: 14px 20px;
  }
  .landing-nav__links {
    display: none;
  }
  .landing-hero {
    padding: 48px 20px 72px;
  }
  .hero-title {
    font-size: 34px;
  }
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  .landing-section {
    padding: 48px 20px;
  }
}
</style>
