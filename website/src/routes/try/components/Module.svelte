<script lang="ts">
	import Single_Point from './Single_Point.svelte';
	import SingleMHB from './SingleMHB.svelte';
	import type { SingleModule, Exam, Expense, ModulePart } from './SingleMHB.svelte';
	export let module: SingleModule;
</script>

<div class="mb-6 rounded-2xl border-3 border-fuchsia-800/60 bg-[#5a045a70]">
	<h2 class="mt-2 mb-3 text-center font-semibold dark:text-white">
		{module.module_code}
	</h2>

	<div
		class="grid grid-cols-[min-content_2px_1fr] gap-x-4 gap-y-3 border-fuchsia-900/10 px-4 py-4 text-left break-words"
	>
		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Titel</p>
		<p class="col-start-3">{module.title}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Modul-Code</p>
		<p class="col-start-3">{module.module_code}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">ECTS</p>
		<p class="col-start-3">{module.ects}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Vortragende</p>
		<p class="col-start-3">{module.lecturer}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Wochenstunden</p>
		<p class="col-start-3">{module.weekly_hours}</p>

		<div class="col-start-2 row-start-1 row-end-[6] w-[2px] bg-fuchsia-900/80"></div>
	</div>
</div>
