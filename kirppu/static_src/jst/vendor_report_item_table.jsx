import {yesNo, title} from "./helpers";

function Total({sum, isExpectedSum}) {
    if (isExpectedSum) {
        return (
            <tr className="hidden-print">
                <th colSpan="4">{gettext("Expected total:")}</th>
                <th className="receipt_price numeric">~ {displayPrice(sum)} ~</th>
                <th/>
                <th/>
            </tr>
        )
    } else {
        return (
            <tr className="hidden-print">
                <th colSpan="4">{gettext("Total:")}</th>
                <th className="receipt_price numeric">{displayPrice(sum)}</th>
                <th/>
                <th/>
            </tr>
        )
    }
}

export default function render({id, items, caption, sum, hidePrint, isExpectedSum}) {
    return (
        <table className={"table table-striped table-hover table-condensed" + (hidePrint ? " hidden-print" : "")}
               id={id}>
            {caption && <caption className={"h3" + (hidePrint ? " text-muted" : "")}>{caption}</caption>}
            <thead>
            <tr>
                <th className="receipt_index numeric">{gettext("#")}</th>
                <th className="receipt_code">{gettext("code")}</th>
                <th className="receipt_item">{gettext("item")}</th>
                <th>{gettext("item type")}</th>
                <th className="receipt_price numeric">{gettext("price")}</th>
                <th className="receipt_status">{gettext("status")}</th>
                <th className="receipt_abandoned">{gettext("abandoned")}</th>
            </tr>
            </thead>
            <tbody>
            {items.map((item, index) =>
                <tr className={"table_row_" + (index + 1) + (item.state === " ST" ? " bg-warning" : "")}>
                    <td className="receipt_index numeric">{index + 1}</td>
                    <td className="receipt_code">{item.code}</td>
                    <td className="receipt_item">{item.name}</td>
                    <td>{item.itemtype_display}</td>
                    <td className="receipt_price numeric">{displayPrice(item.price)}</td>
                    <td className="receipt_status">{item.state_display}</td>
                    <td className="receipt_abandoned">{title(yesNo(item.abandoned))}</td>
                </tr>
            )}
            {!items &&
            <tr>
                <td colSpan="6">{gettext("No items.")}</td>
            </tr>
            }
            {items && <Total sum={sum} isExpectedSum={isExpectedSum}/>}
            </tbody>
        </table>
    )
}
