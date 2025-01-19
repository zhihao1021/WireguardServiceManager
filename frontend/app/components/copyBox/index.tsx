"use client"
import { ReactNode, useCallback, useState } from "react";

import style from "./index.module.scss";

export default function CopyBox(props: Readonly<{
    text: string
}>): ReactNode {
    const {
        text
    } = props;

    const [copySuccess, setCopySuccess] = useState<boolean>(false);

    const onClick = useCallback(() => {
        navigator.clipboard.writeText(text).then(() => {
            setCopySuccess(true);
            setTimeout(() => setCopySuccess(false), 1000);
        })
    }, []);

    return <div
        className={style.copyBox}
        onClick={onClick}
        data-success={copySuccess}
    >
        <span>{text}</span>
        <span className={`ms-p ${style.icon}`} />
    </div>
}