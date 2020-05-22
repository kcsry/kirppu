// In vendor report.

export default function render({items, sums, counts, caption, hidePrint, hideSumInPrint}) {
    return (
        <table className={"table table-striped table-hover table-condensed" + (hidePrint ? " hidden-print" : "")}>
            {caption && <caption className="h3">{caption}</caption>}
            <thead>
            <tr>
                <th className="receipt_index numeric">#</th>
                <th>{gettext("description")}</th>
                <th className="receipt_price numeric">{gettext("price")}</th>
                <th className="receipt_count numeric">{gettext("brought")}</th>
                <th className="receipt_count numeric">{gettext("compensable")}</th>
                <th className="receipt_count numeric">{gettext("compensated")}</th>
                <th className="receipt_count numeric">{gettext("returnable")}</th>
            </tr>
            </thead>
            <tbody>
            {items.map((item, index) =>
                <tr>
                    <td className="receipt_index numeric">{index + 1}</td>
                    <td>{item.description}</td>
                    <td className="receipt_price numeric">{displayPrice(item.item_price)}</td>
                    <td className="receipt_price numeric">{item.items_brought_total}</td>
                    <td className="receipt_price numeric">{item.items_sold}</td>
                    <td className="receipt_price numeric">{item.items_compensated}</td>
                    <td className="receipt_price numeric">{item.items_returnable}</td>
                </tr>
            )}
            {!items &&
            <tr>
                <td colSpan="6">{gettext("No boxes.")}</td>
            </tr>
            }
            {items &&
            <tr className={hideSumInPrint && "hidden-print"}>
                <th colSpan="3">{gettext("Total:")}</th>
                <th className="receipt_price numeric">{displayPrice(sums.brought)} ({counts.brought})</th>
                <th className="receipt_price numeric">{displayPrice(sums.sold)} ({counts.sold})</th>
                <th className="receipt_price numeric"
                    style="font-weight: normal">{displayPrice(sums.compensated)} ({counts.compensated})
                </th>
                <th/>
            </tr>
            }
            </tbody>
        </table>
    )
}
