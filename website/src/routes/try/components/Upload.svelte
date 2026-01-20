<script lang="ts">
	pdf: File;

	import { uploadedFile } from '$lib/uploadStore';

	// pdf_2: File | null = null;

	function handleFileChange(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files.length > 0) {
			processFile(input.files[0]);
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		event.stopPropagation();
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		event.stopPropagation();
		const files = event.dataTransfer?.files;
		if (files && files.length > 0) {
			processFile(files[0]);
		}
	}

	function processFile(file: File) {
		if (file.name.endsWith('.pdf') === false) {
			alert('Bitte eine PDF-Datei auswählen.');
			return;
		}

		console.log('Selected file:', file);
		uploadedFile.set(file);
		// You can now use pdf_1 for further processing, such as uploading it to a server
	}
</script>

<div class="mt-10 mb-4 text-center text-3xl font-semibold dark:text-white">
	Bitte lade ein Modulhandbuch hoch
</div>
<div class="flex items-center justify-center px-12 dark:text-white">
	<label
		for="dropzone-file"
		class="flex h-64 w-lg cursor-pointer
    flex-col items-center justify-center rounded-4xl border-2 border-fuchsia-700/70
    bg-fuchsia-300/70 shadow-[inset_0_8px_14px_rgba(255,0,255,0.7)]
    inset-shadow-fuchsia-950 hover:bg-fuchsia-500/60
    dark:bg-fuchsia-900/70 dark:inset-shadow-fuchsia-300 hover:dark:bg-fuchsia-800/70"
		on:drop={handleDrop}
		on:dragover={handleDragOver}
	>
		<div class="text-body flex flex-col items-center justify-center pt-5 pb-6">
			<svg
				class="mb-4 h-8 w-8"
				aria-hidden="true"
				xmlns="http://www.w3.org/2000/svg"
				width="24"
				height="24"
				fill="none"
				viewBox="0 0 24 24"
				><path
					stroke="currentColor"
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M15 17h3a3 3 0 0 0 0-6h-.025a5.56 5.56 0 0 0 .025-.5A5.5 5.5 0 0 0 7.207 9.021C7.137 9.017 7.071 9 7 9a4 4 0 1 0 0 8h2.167M12 19v-9m0 0-2 2m2-2 2 2"
				/></svg
			>
			<p class="mb-2 text-sm">
				<span class="font-semibold">Klicken für Upload</span> oder Drag and Drop
			</p>
			<p class="text-xs">PDF (MAX 30 MB)</p>
		</div>
		<input
			id="dropzone-file"
			type="file"
			class="hidden"
			multiple={false}
			accept=".pdf"
			on:change={handleFileChange}
		/>
	</label>
</div>
