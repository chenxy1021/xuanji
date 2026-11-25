<script setup lang="ts">
import { computed, ref } from 'vue'
import type { StarKind, ZiweiChart, ZiweiPalace } from '@/api/types'

const props = defineProps<{ chart: ZiweiChart }>()

/**
 * 传统斗数环状布局：十二宫按地支子→亥顺时针排在外圈，
 * 子居下中，与「命宫在子」的常见排盘一致。
 *   巳 午 未 申
 *   辰  ╳  ╳  酉
 *   卯  ╳  ╳  戌
 *   寅 丑 子 亥
 */
const RING = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
// RING 与 [行, 列] 一一对应：子→亥 顺时针绕外圈
const POS: [number, number][] = [
  [4, 3], [4, 2], [4, 1], [3, 1], [2, 1], [1, 1],
  [1, 2], [1, 3], [1, 4], [2, 4], [3, 4], [4, 4],
]
const gridCol = (i: number) => POS[i][1]
const gridRow = (i: number) => POS[i][0]

const palaceMap = computed(() => new Map(props.chart.palaces.map((p) => [p.branch, p])))
const ring = computed(() => RING.map((b) => palaceMap.value.get(b)).filter((p): p is ZiweiPalace => !!p))

function decadeOf(p: ZiweiPalace) {
  return props.chart.decades.find((d) => d.branch === p.branch)
}

function lunarShort(text: string) {
  // 一九九〇年四月廿一 → 四月廿一
  const m = text.match(/年(.+)$/)
  return m ? m[1] : text
}

const KIND_STYLE: Record<StarKind, string> = {
  major: '',
  lucky: 'text-success',
  sha: 'text-danger',
  minor: 'text-muted',
}
const HUA_STYLE: Record<string, string> = {
  禄: 'text-hua-lu',
  权: 'text-hua-quan',
  科: 'text-hua-ke',
  忌: 'text-hua-ji',
}
const SHOW_BRIGHTNESS = ['庙', '旺', '陷']

const mode = ref<'grid' | 'list'>('grid')
const selected = ref<ZiweiPalace | null>(null)

function toggle(p: ZiweiPalace) {
  selected.value = selected.value?.branch === p.branch ? null : p
}

/** 三方四正：本宫 + 对宫（+6）+ 两个三合宫（±4） */
const relatedBranches = computed(() => {
  if (!selected.value) return new Set<string>()
  const i = RING.indexOf(selected.value.branch)
  if (i < 0) return new Set<string>()
  return new Set([0, 4, 6, 8].map((step) => RING[(i + step) % 12]))
})

const relatedPalaces = computed(() => {
  if (!selected.value) return []
  const i = RING.indexOf(selected.value.branch)
  if (i < 0) return []
  return [4, 6, 8]
    .map((step) => palaceMap.value.get(RING[(i + step) % 12]))
    .filter((p): p is ZiweiPalace => !!p)
})

const majorOf = (p: ZiweiPalace) => p.stars.filter((s) => s.kind === 'major').slice(0, 2)
const minorOf = (p: ZiweiPalace) => p.stars.filter((s) => s.kind !== 'major')

const sihuaPairs = computed(() => Object.entries(props.chart.sihua))
</script>

<template>
  <div class="space-y-4">
    <!-- 概要 -->
    <div class="flex flex-wrap items-center gap-1.5">
      <span class="chip chip--primary">命宫 {{ chart.ming_gong }}</span>
      <span class="chip">身宫 {{ chart.shen_gong }}</span>
      <span class="chip">{{ chart.bureau }}</span>
      <span class="chip tabular">虚岁 {{ chart.current_age }}</span>
      <button
        type="button"
        class="btn-ghost ml-auto"
        @click="mode = mode === 'grid' ? 'list' : 'grid'"
      >
        切{{ mode === 'grid' ? '列表' : '宫格' }}
      </button>
    </div>

    <!-- 宫格 -->
    <div
      v-if="mode === 'grid'"
      role="grid"
      aria-label="紫微十二宫"
      class="grid grid-cols-4 grid-rows-4 gap-px overflow-hidden border border-line-strong bg-line [grid-auto-rows:minmax(118px,1fr)] sm:[grid-auto-rows:minmax(138px,1fr)]"
    >
      <button
        v-for="(p, i) in ring"
        :key="p.branch"
        type="button"
        role="gridcell"
        class="relative flex min-w-0 flex-col gap-[3px] p-2 pb-5 text-left transition-[background-color,box-shadow,opacity] duration-150 active:bg-surface-2"
        :class="[
          p.is_ming ? 'bg-accent-soft' : 'bg-surface',
          selected?.branch === p.branch
            ? 'z-10 shadow-[inset_0_0_0_2px_var(--color-text)]'
            : relatedBranches.has(p.branch)
              ? 'bg-surface-2 shadow-[inset_0_0_0_1px_var(--color-text-muted)]'
              : selected
                ? 'opacity-55'
                : '',
        ]"
        :style="{ gridColumn: gridCol(i), gridRow: gridRow(i) }"
        :aria-label="`${p.name} ${p.stem}${p.branch}`"
        :aria-pressed="selected?.branch === p.branch"
        :data-selected="selected?.branch === p.branch ? 'true' : 'false'"
        :data-related="relatedBranches.has(p.branch) ? 'true' : 'false'"
        @click="toggle(p)"
      >
        <span class="flex items-start justify-between gap-1">
          <span class="truncate font-serif text-[13px] leading-tight text-ink-2" :class="p.is_ming ? 'font-medium text-accent' : ''">
            {{ p.name }}
          </span>
          <span v-if="p.is_shen" class="mt-1 size-[5px] shrink-0 rounded-full bg-accent" title="身宫" />
        </span>
        <span class="flex min-w-0 flex-wrap gap-x-1.5 gap-y-0.5">
          <template v-if="majorOf(p).length">
            <span
              v-for="s in majorOf(p)"
              :key="s.name"
              class="whitespace-nowrap font-serif text-[17px] leading-[1.3]"
            >
              {{ s.name }}<sup
                v-if="s.brightness && SHOW_BRIGHTNESS.includes(s.brightness)"
                class="ml-px font-sans text-[12px] text-muted"
              >{{ s.brightness }}</sup><i
                v-if="s.sihua"
                class="ml-px inline-block rounded-[3px] border px-[2px] align-[2px] font-sans text-[13px] not-italic leading-[1.3]"
                :class="HUA_STYLE[s.sihua]"
              >{{ s.sihua }}</i>
            </span>
          </template>
          <span v-else class="font-serif text-[13px] text-muted">无主星</span>
        </span>
        <span class="flex min-w-0 flex-wrap gap-x-1 text-[13px] leading-[1.4] text-muted">
          <span v-for="s in minorOf(p).slice(0, 3)" :key="s.name" class="whitespace-nowrap" :class="KIND_STYLE[s.kind]">{{ s.name }}</span>
          <span v-if="minorOf(p).length > 3" class="whitespace-nowrap">+{{ minorOf(p).length - 3 }}</span>
        </span>
        <span class="tabular absolute bottom-[3px] left-[6px] text-[13px] text-muted">
          {{ decadeOf(p) ? `${decadeOf(p)!.start_age}–${decadeOf(p)!.end_age}` : '' }}
        </span>
        <span class="absolute right-[6px] bottom-[3px] text-[13px] text-muted opacity-80">{{ p.branch }}</span>
      </button>

      <!-- 中心 2×2 -->
      <div
        class="flex flex-col justify-center gap-1.5 bg-bg-subtle p-3"
        style="grid-column: 2 / 4; grid-row: 2 / 4"
      >
        <p class="text-center font-serif text-[15px] leading-tight">
          紫微在{{ chart.ming_gong }}
          <span class="mt-0.5 block font-sans text-[13px] text-muted">身宫 · {{ chart.shen_gong }}</span>
        </p>
        <dl class="space-y-1 text-[13px] text-muted">
          <div class="flex items-baseline justify-between gap-2">
            <dt>性别</dt>
            <dd class="text-[13px] font-medium text-ink">{{ chart.gender }}</dd>
          </div>
          <div class="flex items-baseline justify-between gap-2">
            <dt>农历</dt>
            <dd class="text-right text-[12px] text-ink">{{ lunarShort(chart.lunar_date) }}</dd>
          </div>
          <div v-for="(pair, idx) in [sihuaPairs.slice(0, 2), sihuaPairs.slice(2, 4)]" :key="idx" class="flex justify-between gap-2">
            <dt>{{ idx === 0 ? '四化' : '' }}</dt>
            <dd class="text-right text-[13px] text-ink">
              <span v-for="[hua, star] in pair" :key="hua" class="ml-1">{{ hua }}{{ star }}</span>
            </dd>
          </div>
        </dl>
      </div>
    </div>

    <!-- 列表模式 -->
    <ul v-else class="overflow-hidden border border-line-strong bg-line">
      <li v-for="p in ring" :key="p.branch">
        <button
          type="button"
          class="flex min-h-[52px] w-full items-center gap-3 bg-surface px-3 py-2 text-left active:bg-surface-2"
          :class="p.is_ming ? 'bg-accent-soft' : ''"
          @click="toggle(p)"
        >
          <span class="w-14 shrink-0 text-[13px]" :class="p.is_ming ? 'font-medium text-accent' : 'text-ink-2'">
            {{ p.name }}
          </span>
          <span class="flex min-w-0 flex-1 flex-wrap gap-x-2">
            <span v-for="s in p.stars" :key="s.name" class="whitespace-nowrap text-[14px]" :class="KIND_STYLE[s.kind]">
              {{ s.name }}<i v-if="s.sihua" class="ml-0.5 text-[13px] not-italic" :class="HUA_STYLE[s.sihua]">{{ s.sihua }}</i>
            </span>
          </span>
          <span class="tabular shrink-0 text-[13px] text-muted">
            {{ decadeOf(p) ? `${decadeOf(p)!.start_age}-${decadeOf(p)!.end_age}` : '' }}
          </span>
          <span class="w-4 shrink-0 text-[13px] text-muted">{{ p.branch }}</span>
        </button>
      </li>
    </ul>

    <!-- 图例 -->
    <ul class="flex flex-wrap gap-x-2.5 gap-y-1 text-[13px] text-muted">
      <li v-for="[hua, star] in sihuaPairs" :key="hua" class="inline-flex items-center gap-1">
        <span class="inline-block rounded-[3px] border px-[2px] leading-[1.2]" :class="HUA_STYLE[hua]">{{ hua }}</span>
        化{{ hua }}
        <span class="text-ink-2">{{ star }}</span>
      </li>
      <li class="w-full">·<span class="text-success">吉星</span> ·<span class="text-danger">煞星</span> · 灰色为辅星；点宫位高亮三方四正并看全部星曜</li>
    </ul>

    <!-- 宫位详情 -->
    <section
      v-if="selected"
      class="border-t border-line-strong pt-3"
      data-ziwei-detail="on"
    >
      <div class="mb-2 flex items-baseline justify-between">
        <p class="text-[14px] font-medium">
          {{ selected.name }}
          <small class="ml-1.5 text-[13px] font-normal text-muted">{{ selected.stem }}{{ selected.branch }}</small>
        </p>
        <button type="button" class="btn-ghost" @click="selected = null">收起</button>
      </div>
      <dl class="space-y-1 text-[12px]">
        <div class="flex gap-2">
          <dt class="w-9 shrink-0 text-muted">大限</dt>
          <dd class="text-ink-2">{{ decadeOf(selected) ? `${decadeOf(selected)!.start_age}-${decadeOf(selected)!.end_age} 岁` : '—' }}</dd>
        </div>
        <div class="flex gap-2">
          <dt class="w-9 shrink-0 text-muted">星曜</dt>
          <dd class="flex flex-wrap gap-x-2 text-ink-2">
            <span v-for="s in selected.stars" :key="s.name" :class="KIND_STYLE[s.kind]">
              {{ s.name }}<span v-if="s.brightness" class="text-muted">·{{ s.brightness }}</span>
              <i v-if="s.sihua" class="not-italic" :class="HUA_STYLE[s.sihua]"> 化{{ s.sihua }}</i>
            </span>
            <span v-if="!selected.stars.length">无</span>
          </dd>
        </div>
        <div class="flex gap-2">
          <dt class="w-9 shrink-0 text-muted">状态</dt>
          <dd class="text-ink-2">
            {{ selected.is_ming || selected.is_shen ? [selected.is_ming ? '命宫' : '', selected.is_shen ? '身宫' : ''].filter(Boolean).join(' · ') : '普通宫位' }}
          </dd>
        </div>
        <div v-if="relatedPalaces.length" class="flex gap-2">
          <dt class="w-9 shrink-0 text-muted">三方四正</dt>
          <dd class="text-ink-2">
            {{ relatedPalaces.map((p) => `${p.name}（${p.branch}）`).join(' · ') }}
          </dd>
        </div>
      </dl>
    </section>

    <!-- 大限列表 -->
    <section class="border-t border-line-strong pt-4">
      <h3 class="form-label">大限</h3>
      <div class="scroll-x">
        <table class="w-full text-center text-[13px]">
          <thead>
            <tr class="border-b border-line-strong text-xs text-muted">
              <th scope="col" class="px-2 py-1.5 font-medium">宫位</th>
              <th scope="col" class="px-2 py-1.5 font-medium">地支</th>
              <th scope="col" class="px-2 py-1.5 font-medium">年龄段</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="d in chart.decades"
              :key="d.branch"
              class="border-t border-line"
              :class="chart.current_decade?.branch === d.branch ? 'text-accent' : ''"
            >
              <td class="px-2 py-2">{{ d.palace }}</td>
              <td class="px-2 py-2">{{ d.branch }}</td>
              <td class="tabular whitespace-nowrap px-2 py-2">{{ d.start_age }}-{{ d.end_age }} 岁</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
