<script lang="ts">
	import Header from '../../components/Header.svelte';
    let module: string = '';
    async function searchModule() {
        const response = await fetch('/api/get-module', {
			method: 'POST',
            headers: {
                'Content-Type': 'text/plain'
            },
			body: module
		});
    }
</script>

<Header link="/module-library" />

<form class="mb-12 flex flex-wrap justify-center mt-5" on:submit|preventDefault={searchModule}>
    <input bind:value={module}
        class="w-[50rem] rounded-full border-3 border-fuchsia-500 bg-fuchsia-900/40 py-6 text-center text-lg
    shadow-[inset_0_0_10px_#16a34a] inset-shadow-sm hover:bg-fuchsia-900/60
    focus:bg-fuchsia-900/60 focus:shadow-[inset_0_0_10px_#18181b] focus:ring-0 focus:outline-none"
        placeholder="Modulsuche"
    />
</form>