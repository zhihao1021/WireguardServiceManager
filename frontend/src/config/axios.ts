import axios from "axios";

const req = axios.create();
req.interceptors.request.use(async (config) => {
    config.baseURL = import.meta.env.VITE_API_END_POINT;

    let token = localStorage.getItem("access_token");
    let tokenType = localStorage.getItem("token_type");
    // if JWT exist, put it into header
    if (token !== null && tokenType !== null) {
        config.headers.Authorization = `${tokenType} ${token}`;
    }
    return config;
});

export default req;
