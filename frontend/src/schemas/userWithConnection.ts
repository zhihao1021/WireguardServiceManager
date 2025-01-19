import UserData from "./userData";

export default interface UserWithConnection extends UserData {
    connection: {
        public_key: string,
        ip_address: string,
    }
};
