<script lang="ts">
	let item: Array<string>;
</script>

<div>
	{#if Array.isArray(item[1])}
		<ul class="list-disc">
			{#each item[1] as subitem}
				<li>{subitem}</li>
			{/each}
		</ul>
	{:else}
		<p>{item[1]}</p>
	{/if}
</div>
