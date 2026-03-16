import type { RequestHandler } from "@sveltejs/kit";
import { json } from "@sveltejs/kit";

export const POST: RequestHandler = async ({ request }) => {
  try {
    const search = await request.text();

    if (!search) {
      return new Response("No search term provided", { status: 400 });
    }

    const formData = new FormData();
    formData.append("search", search);

    const response = await fetch('http://127.0.0.1:5000/api/get_module', {
      method: 'POST',
      body: formData
    });
    if (!response.ok) {
      return new Response('Backend error', { status: 500 });
    }

    const data = await response.json();

    return json(data);
  } catch (err) {
    return new Response('Server error', { status: 500 });
  }
};
