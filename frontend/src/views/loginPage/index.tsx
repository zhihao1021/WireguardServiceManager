import { ChangeEvent, KeyboardEvent, ReactNode, useCallback, useEffect, useState } from "react";

import req from "@/config/axios";
import JWT from "@/schemas/jwt";

import style from "./index.module.scss";
import { useNavigate, useSearchParams } from "react-router-dom";

export default function LoginPage(): ReactNode {
    const [loading, setLoading] = useState<boolean>(false);
    const [code, setCode] = useState<string | null>();
    const [joinKey, setJoinKey] = useState<string>("");

    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();

    const onJoinKeyChage = useCallback((event: ChangeEvent<HTMLInputElement>) => {
        setJoinKey(event.target.value);
    }, []);

    const onKeyDown = useCallback((event: KeyboardEvent<HTMLInputElement>) => {
        if (event.key !== "Enter" || code === null) return;

        setLoading(true);
        req.post(
            "/oauth", { code: code, join_key: joinKey }
        ).then(response => {
            const data = response.data as JWT;
            localStorage.setItem("token_type", data.token_type);
            localStorage.setItem("access_token", data.access_token);
            navigate("/");
        }).catch(() => {
            setCode(null);
            setJoinKey("");
            setLoading(false);
        })
    }, [code, joinKey, navigate]);

    useEffect(() => {
        const params = searchParams;
        const code = params.get("code");
        params.delete("code");
        if (code) setSearchParams(params);
        setCode(current => {
            return current ?? code
        });
    }, [location.search, searchParams, setSearchParams]);

    return <div className={style.loginPage}>
        <div className={style.box}>
            <h1>Login</h1>
            <div className={style.content} data-loading={loading || code === undefined}>
                <div className={style.loading} />
                {
                    code == null ? <a href={import.meta.env.VITE_OAUTH_URL ?? ""}>
                        <img src="/discord-logo-white.svg" />
                    </a> : <div className={style.joinKey}>
                        <div className={style.inputBox}>
                            <span className="ms">key</span>
                            <input
                                value={joinKey}
                                onChange={onJoinKeyChage}
                                onKeyDown={onKeyDown}
                                placeholder="Join Key"
                            />
                        </div>
                        <div className={style.info}>If you have logged in before, please press Enter directly.</div>
                    </div>
                }
            </div>
        </div>
    </div>
}