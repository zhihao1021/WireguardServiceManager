import { jwtDecode } from "jwt-decode";
import { ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import req from "@/config/axios";
import JWT from "@/schemas/jwt";
import UserData from "@/schemas/userData";
import UserWithConnection from "@/schemas/userWithConnection";
import { timeParser } from "@/utils/timeParser";


import CopyBox from "@/components/copyBox";

import style from "./index.module.scss";

const env = import.meta.env;

async function getUserData(): Promise<UserData> {
    const token = localStorage.getItem("access_token");
    let data: UserData = jwtDecode(token as string);
    if (data.exp * 1000 < Date.now()) {
        throw Error("Token expired");
    }

    if (data.exp * 1000 - Date.now() < 72 * 3600 * 1000) {
        const response = await req.put("/oauth");
        const jwt: JWT = response.data;
        localStorage.setItem("token_type", jwt.token_type);
        localStorage.setItem("access_token", jwt.access_token);
        data = jwtDecode(jwt.access_token);
    }

    return data;
}

async function getUsers(): Promise<Array<UserWithConnection>> {
    const response = await req.get("/connection");
    return response.data;
}

async function getConnectionString(): Promise<string> {
    const response = await req.get("/connection/connect");
    return btoa(response.data);
}

function getStatus(key: string, status?: { [key: string]: number }): "live" | "dead" | "unknow" {
    console.log(key)
    console.log(status);
    if (status === undefined || status[key] === undefined) return "unknow";
    const delta = Date.now() - (status[key] * 1000);
    if (delta > 180 * 1000) return "dead";
    return "live";
}

export default function HomePage(): ReactNode {
    const [userData, setUserData] = useState<UserData>();
    const [connectionString, setConnectionString] = useState<string>("");
    const [userList, setUserList] = useState<Array<UserWithConnection>>([]);
    const [status, setStatus] = useState<{ [publicKey: string]: number }>();
    const [, setWs] = useState<WebSocket>();

    const navigate = useNavigate();

    const userConnectionInfo: UserWithConnection | undefined = useMemo(() => {
        return Object.assign({
            connection: {
                public_key: "",
                ip_address: "192.16.255.255"
            }
        }, userData) as UserWithConnection;

        return userList.find(v => v.discord_id == userData?.discord_id);
    }, [userData, userList]);

    const connectWs = useCallback(() => {
        let endPoint = env.VITE_API_END_POINT;
        if (endPoint === undefined)
            return;

        if (!endPoint.startsWith("http"))
            endPoint = `${location.origin}${endPoint}`;

        const ws = new WebSocket(`${endPoint.replace("http", "ws")}/connection/ws`);
        ws.onopen = () => ws.send(localStorage.getItem("access_token") ?? "")
        ws.onmessage = message => {
            const rawData: Blob = message.data;
            rawData.text().then(dataString => setStatus(JSON.parse(dataString)));
        }
        ws.onerror = () => ws.close();
        ws.onclose = () => {
            setTimeout(connectWs, 1000);
        };
        setWs(ws);
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem("token_type");
        localStorage.removeItem("access_token");
        navigate("/login");
    }, [navigate]);

    useEffect(() => {
        getUserData().then(userData => {
            setUserData(userData)
            getUsers().then(response => setUserList(response));
            getConnectionString().then(response => setConnectionString(response));
            connectWs();
        }).catch(() => {
            navigate("/login");
        })
    }, [connectWs]);

    if (userData === undefined)
        return undefined;

    return <div className={style.home}>
        <div className={style.userInfo}>
            <img src={userData.display_avatar} />
            <div className={style.displayName}>{userData.display_name}</div>
            <div className={style.functions}>
                <div className={style.ipAddress}>
                    {
                        userConnectionInfo ? <CopyBox
                            text={userConnectionInfo.connection.ip_address}
                        /> : undefined
                    }
                </div>
                <a
                    href={`data:text/plain;base64,${connectionString}`}
                    download="connection.conf"
                    target="_blank"
                    className={style.conf}
                >
                    <span className="ms">download</span>
                    <span>Conf.</span>
                </a>
                <a
                    href={env.VITE_WIREGUARD_LINK}
                    target="__blank"
                    className={style.install}
                >
                    <span className="ms">open_in_new</span>
                    <span>Install</span>
                </a>
                <button className={style.logout} onClick={logout}>
                    <span className="ms">logout</span>
                    <span>Logout</span>
                </button>
            </div>
        </div>
        <div className={style.clients}>
            {
                userList.map(data => <div
                    key={data.connection.public_key}
                    className={style.statusBox}
                >
                    <div className={style.user}>
                        <img src={data.display_avatar} />
                        <div>{data.display_name}</div>
                        <div
                            className={style.status}
                            data-live={
                                getStatus(data.connection.public_key, status)
                            }
                        />
                    </div>
                    <hr />
                    <div className={style.userIp}>
                        <div className={style.key}>IP</div>
                        <CopyBox text={data.connection.ip_address} />
                    </div>
                    <div className={style.publicKey}>
                        <div className={style.key}>Public Key</div>
                        <div
                            className={style.value}
                            title={data.connection.public_key}
                        >{data.connection.public_key}</div>
                    </div>
                    <div className={style.lastHandshakes}>
                        <div className={style.key}>Last Seen</div>
                        <div
                            className={style.value}
                        >{status ? timeParser(status[data.connection.public_key]) : "Loading..."}</div>
                    </div>
                </div>)
            }
        </div>
    </div>
}