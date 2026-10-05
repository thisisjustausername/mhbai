<script lang="ts">
	export let type: 'button' | 'href';
	export let link: string;
	export let name: string;
</script>

{#if type === 'href'}
	<a
		href={link}
		class="btn btn-outline btn-primary btn-md inset-shadow-md fuchsia-950 rounded-full border-3 border-fuchsia-500 bg-fuchsia-700/20 px-4 py-1 inset-shadow-sm dark:text-white dark:inset-shadow-fuchsia-300"
	>
		<p>{name}</p>
	</a>

	<!-- TODO: Add functionality for button type -->
{:else if type === 'button'}
	<button
		type="button"
		class="btn btn-outline btn-primary btn-md inset-shadow-md fuchsia-950 rounded-full border-3 border-fuchsia-500 bg-fuchsia-700/20 px-4 py-1 inset-shadow-sm dark:text-white dark:inset-shadow-fuchsia-300"
	>
		<p>{name}</p>
	</button>
{/if}
