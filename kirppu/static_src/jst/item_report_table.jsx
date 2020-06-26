import {dateTime, yesNo, title} from "./helpers";

function Total({sum, extra_col, hide_status}) {
    let price
    if (sum < 0 && !hide_status) {
        price = [
            <span className="glyphicon glyphicon-warning-sign warn-blink"
                  title={gettext("Vendor must pay!")}/>
            , " "
            , displayPrice(sum)
        ]
    } else {
        price = displayPrice(sum)
    }
    return (
        <tr className={sum < 0 ? "danger" : ""}>
            <th colSpan="3">{gettext("Total:")}</th>
            <th className="receipt_price numeric">{price}</th>
            {!hide_status && <th/>}
            {!hide_status && <th/>}
            {extra_col && <th className="receipt_extra_col"/>}
        </tr>
    )
}

function Row({item, index, hide_status, extra_col}) {
    if (item.action !== "EXTRA") {
        return (
            <tr className={"table_row_" + (index + 1) + (item.state === "ST" ? " bg-warning" : "")}>
                <td className="receipt_index numeric">{index + 1}</td>
                <td className="receipt_code">{item.box_number ? item.box_code + "/#" + item.box_number : item.code}</td>
                <td className="receipt_item">{item.description ? item.description : item.name}</td>
                <td className="receipt_price numeric">{displayPrice(item.price)}</td>
                {!hide_status && <td className="receipt_status">{item.state_display}</td>}
                {!hide_status && <td className="receipt_abandoned">{title(yesNo(item.abandoned))}</td>}
                {extra_col && <td className="receipt_extra_col"/>}
            </tr>
        )
    } else {
        return (
            <tr className={"table_row_" + (index + 1) + (item.state === "ST" ? " bg-warning" : "")}>
                <td colSpan="3">{item.type_display}</td>
                <td className="receipt_price numeric">{displayPrice(item.value)}</td>
                {!hide_status && <td colSpan="2"/>}
                {extra_col && <td className="receipt_extra_col"/>}
            </tr>
        )
    }
}


export default function render({items, extra_col, hide_status, time, caption, sum, hidePrint, id}) {
    return [
        <style type="text/css">
            .table-condensed > thead > tr > th,
            .table-condensed > tbody > tr > th,
            .table-condensed > thead > tr > td,
            .table-condensed > tbody > tr > td {"{"}
                padding: 2px;
            {"}"}
        </style>,
        <table className={"table table-striped table-hover table-condensed" + (hidePrint ? " hidden-print" : "")}
               id={id}>
            {caption && <caption className="h3">{caption}</caption>}
            {time && <caption>{dateTime(time)}</caption>}
            <thead>
            <tr>
                <th className="receipt_index numeric">{gettext("#")}</th>
                <th className="receipt_code">{gettext("code")}</th>
                <th className="receipt_item">{gettext("item")}</th>
                <th className="receipt_price numeric">{gettext("price")}</th>
                {!hide_status && <th className="receipt_status">{gettext("status")}</th>}
                {!hide_status && <th className="receipt_abandoned">{gettext("abandoned")}</th>}
                {extra_col && <th className="receipt_extra_col"/>}
            </tr>
            </thead>
            <tbody>

            {items && items.length && <Total sum={sum} extra_col={extra_col} hide_status={hide_status}/>}

            {items.map((item, index) =>
                <Row item={item} index={index} hide_status={hide_status} extra_col={extra_col}/>)}

            {(!items || items.length === 0) &&
            <tr>
                <td colSpan={extra_col ? 7 : 6}>{gettext("No items.")}</td>
            </tr>
            }

            {items && items.length && <Total sum={sum} extra_col={extra_col} hide_status={hide_status}/>}
            </tbody>
        </table>
    ]
}
