export const recommendOutfit = async (userId, formData) => {
    const requestBody = {
        situation: formData.occasion,
        date: formData.time,
        place: formData.place,
        useOnlyClosetItems: formData.onlyCloset
    };
  
    const response = await fetch(`${import.meta.env.VITE_API_URL}/recommendation`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "FitU-User-UUID": userId
        },
        body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
        throw new Error();
    }

    return await response.json();
};