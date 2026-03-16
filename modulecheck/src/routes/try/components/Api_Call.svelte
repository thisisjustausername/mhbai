<script lang="ts">
	file: File;
	async function get_mhb_info(file: File) {
		// make a post request to the api
		const response = await fetch('http://127.0.0.1:5000/api/get_mhb_info', {
			method: 'POST',
			headers: { 'Content-Type': 'application/pdf' },
			body: file
		});
		const data = await response.json();
		console.log(data);
		return data;
	}
</script>
