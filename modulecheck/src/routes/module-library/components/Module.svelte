<script lang="ts">
const { module } = $props<{ module }>();
</script>

<div class="w-full mb-15 rounded-2xl dark:border-1 dark:from-blue-800/10 dark:to-blue-800/10
bg-gradient-to-br from-fuchsia-700 to-cyan-400 p-[2px] dark:p-[0px] 
shadow-[_0_0_20px_rgba(0,0,0,0.5)] dark:border-cyan-400 dark:shadow-[inset_0_0_40px_#1e40af]">
	<h2 class="mt-2 mb-3 text-center font-semibold mt-8">
		{module.module_code}
	</h2>

	<div
		class="grid grid-cols-[min-content_2px_1fr] gap-x-4 gap-y-4 border-fuchsia-900/10 px-10 mb-8 text-left break-words whitespace-pre-line"
	>
		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Titel</p>
		<p class="col-start-3">{module.title}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Modul-Code</p>
		<p class="col-start-3">{module.module_code}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">ECTS</p>
		<p class="col-start-3">{module.ects}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Vortragende</p>
		<p class="col-start-3">{module.lecturer}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Inhalte</p>
		<p class="col-start-3">{Array.isArray(module.contents) && module.contents.length ? module.contents.join('\n') : '-'}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Ziele</p>
		<p class="col-start-3">{Array.isArray(module.goals) && module.goals.length ? module.goals.join('\n') : '-'}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Voraussetzungen</p>
		<p class="col-start-3">{Array.isArray(module.requirements) && module.requirements.length ? module.requirements.join('\n') : '-'}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Aufwand (Aufwand; Inhalt)</p>
		<p class="col-start-3">{Array.isArray(module.expense) && module.expense.length ? module.expense.map((expense) => expense.hours + '; ' + expense.activity).join('\n') : '-'}</p>	

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Bestehensvoraussetzungen</p>
		<p class="col-start-3">{Array.isArray(module.success_requirements) && module.success_requirements.length ? module.success_requirements.join('\n') : '-'}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Wochenstunden</p>
		<p class="col-start-3">{module.weekly_hours}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Empfohlenes Semester</p>
		<p class="col-start-3">{module.recommended_semester}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Prüfungsleistungen (Typ; Dauer)</p>
		<p class="col-start-3">{Array.isArray(module.exams) && module.exams.length ? module.exams.map((exam) => exam.exam_type + '; ' + exam.duration).join('\n') : '-'}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Modulteile (Titel; Sprache; Lehrmethoden)</p>
		<p class="col-start-3">{Array.isArray(module.module_parts) && module.module_parts.length ? module.module_parts.map((part) => part.title + '; ' + part.language + '; ' + part.teaching_methods).join('\n') : '-'}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Version</p>
		<p class="col-start-3">{module.version}</p>

		<p class="col-start-1 border-transparent whitespace-nowrap dark:text-white">Confidence Score</p>
		<p class="col-start-3">{Number(module.confidence_score*100).toFixed(0) + ' %'}</p>


		<div class="col-start-2 row-start-1 row-end-[16] w-[2px] bg-fuchsia-900/80 dark:bg-cyan-800/70"></div>
	</div>
</div>