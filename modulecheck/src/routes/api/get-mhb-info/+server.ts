import type { RequestHandler } from "@sveltejs/kit";
import { json } from "@sveltejs/kit";

export const POST: RequestHandler = async ({ request }) => {
  try {
    const incomingForm = await request.formData();
    const file = incomingForm.get("file");

    if (!(file instanceof File)) {
      return new Response("No file provided", { status: 400 });
    }

    const formData = new FormData();
    formData.append("file", file, file.name)

    const response = await fetch('http://127.0.0.1:5000/api/get_mhb_info', {
      method: 'POST',
      body: formData
    });
    if (!response.ok) {
      return response;
      return new Response('Backend error', { status: 500 });
    }

    const data = await response.json();

    return json(data);
  } catch (err) {
    console.error(err); // TODO: remove this after div
    return new Response('Server error', { status: 500 });
  }
};
