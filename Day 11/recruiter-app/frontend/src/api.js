export const uploadJD = async (file) => {
  const fd = new FormData();
  fd.append("file", file);

  return fetch("http://localhost:8000/upload-jd", {
    method: "POST",
    body: fd
  }).then(res => res.json());
};

export const uploadResumes = async (files) => {
  const fd = new FormData();
  files.forEach(f => fd.append("files", f));

  return fetch("http://localhost:8000/upload-resumes", {
    method: "POST",
    body: fd
  }).then(res => res.json());
};