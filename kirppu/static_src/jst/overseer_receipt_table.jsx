import ResultTable from "./result_table.jsx";

export function overseer_receipt_table() {
    return (
        <ResultTable head={
            <tr>
                <th className="receipt_index">#</th>
                <th>{gettext("counter")}</th>
                <th>{gettext("clerk")}</th>
                <th>{gettext("start time")}</th>
                <th className="receipt_price">{gettext("total")}</th>
                <th>{gettext("status")}</th>
            </tr>
        }/>
    )
}

export function overseer_receipt_table_item({item, index}) {
    return (
        <tr className="receipt_tr_clickable">
            <td className="receipt_index numeric">{index}</td>
            <td>{item.counter}</td>
            <td>{item.clerk.print}</td>
            <td>{DateTimeFormatter.datetime(item.start_time)}</td>
            <td className="receipt_price numeric">{displayPrice(item.total)}</td>
            <td>{item.status_display}</td>
        </tr>
    )
}

export function overseer_receipt_table_no_results() {
    return (
        <tr>
            <td/>
            <td colSpan="5">{gettext("No results.")}</td>
        </tr>
    )
}
