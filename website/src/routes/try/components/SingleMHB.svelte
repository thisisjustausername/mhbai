<script lang="ts" context="module">
	export type SingleModule = {
		title: string | null;
		module_code: string;
		ects: number | null;
		lecturer: string | null;
		contents: Array<string> | string | null;
		goals: Array<string> | string | null;
		requirements: Array<string> | string | null;
		expense: Array<Expense> | null;
		success_requirements: Array<string> | null;
		weekly_hours: number | null;
		recommended_semester: number | null;
		exams: Array<Exam> | null;
		module_parts: Array<ModulePart> | null;
		credibility: number;
	};

	export type Expense = {
		activity: string | null;
		hours: number | null;
	};

	export type Exam = {
		exam_type: string | null;
		exam_info: Array<string> | null;
		duration: number | null;
	};

	export type ModulePart = {
		title: string | null;
		language: string | null;
		teaching_methods: Array<string> | null;
	};
</script>

<script lang="ts">
	import Module from './Module.svelte';

	export let mhb;

	let information: string;
	let data: SingleModule;
	let module_limit: number | null = null;

	$: if ('information' in mhb) {
		information = mhb.information as string;
		console.log(information);
		if (information != null && information.includes('LIMITED TO ')) {
			module_limit = Number.parseInt(information.split('LIMITED TO ', 2)[1].split(' ', 2)[0]);
		}
	}
</script>

<div
	class="mt-8 bg-gradient-to-b from-white via-fuchsia-500 to-amber-500 dark:bg-black
  dark:bg-gradient-to-b dark:from-black dark:via-fuchsia-700/80 dark:to-fuchsia-900/30 dark:text-white"
>
	<div
		class="mx-auto mb-6 max-w-3xl rounded-2xl border-3 border-fuchsia-800 bg-fuchsia-900 p-6
    text-center text-gray-800 dark:border-fuchsia-400 dark:bg-[#64006480]
    dark:text-gray-200 dark:shadow-[inset_0_0_25px_rgba(255,0,255,0.7)] dark:inset-shadow-fuchsia-950"
	>
		<h2 class="mb-2 text-2xl font-bold">Modulhandbuch Übersicht</h2>
		{#if module_limit != null}
			<p class="dark:text-red-500">
				Limitert auf {module_limit}
				{module_limit === 1 ? 'Modul' : 'Module'}
			</p>
		{/if}
	</div>
	<div
		class="mx-auto max-w-3xl rounded-2xl border-3 border-fuchsia-800 bg-fuchsia-300 p-6
    shadow-[inset_0_0_25px_rgba(255,0,255,0.7)] inset-shadow-fuchsia-950 dark:border-fuchsia-400
    dark:bg-[#64006460]
"
	>
		{#each mhb.data as module}
			<Module module={module as SingleModule} />
			<!-- <grid class="black:text-white rounded-2xl border-2 border-fuchsia-800"> </grid> -->
		{/each}
	</div>
</div>
