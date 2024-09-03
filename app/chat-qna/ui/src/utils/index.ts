const documentToBase64 = (document: File) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(document);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });

export { documentToBase64 };
