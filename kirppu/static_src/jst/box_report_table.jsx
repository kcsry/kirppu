// In vendor report.

function BoxRows({item}) {
    if (item.type === "groupHead") {
        return (
            <tr>
                <td rowSpan={item.count + 1} className="receipt_index numeric">{item.index}</td>
                <td rowSpan={item.count + 1}>{item.description}</td>
                <td className="receipt_price numeric">{gettext("Total:")}</td>
                <td className="receipt_price numeric">{item.brought}</td>
                <td className="receipt_price numeric">{item.sold}</td>
                <td className="receipt_price numeric">{item.compensated}</td>
                <td className="receipt_price numeric">{item.returnable}</td>
            </tr>
        )
    } else if (item.type === "groupItem") {
        return (
            <tr className="table-row-groupItem">
                {/* First two cells are row-spanned. */}
                <td className="receipt_price numeric">{displayPrice(item.price)}</td>
                <td className="receipt_price numeric"/>
                <td className="receipt_price numeric">{item.sold}</td>
                <td className="receipt_price numeric">{item.compensated}</td>
                <td className="receipt_price numeric"/>
            </tr>
        )
    } else if (item.type === "single") {
        return (
            <tr>
                <td className="receipt_index numeric">{item.index}</td>
                <td>{item.description}</td>
                <td className="receipt_price numeric">{displayPrice(item.price)}</td>
                <td className="receipt_price numeric">{item.brought}</td>
                <td className="receipt_price numeric">{item.sold}</td>
                <td className="receipt_price numeric">{item.compensated}</td>
                <td className="receipt_price numeric">{item.returnable}</td>
            </tr>
        )
    }
}

export default function render({items, sums, counts, caption, hidePrint, hideSumInPrint}) {
    // Flatten nested items array
    const rows = items.flatMap((item, index) => {
        const prices = Object.keys(item.counts)
        if (prices.length === 1) {
            const detail = item.counts[prices[0]]
            return [{
                type: "single",
                index: index + 1,
                description: item.description,
                price: Number.parseInt(prices[0]),
                brought: item.items_brought_total,
                sold: detail.items_sold,
                compensated: detail.items_compensated,
                returnable: item.items_returnable,
            }]
        } else {
            const sums = {
                sold: 0,
                compensated: 0,
            }
            const r = prices.map((e) => {
                const detail = item.counts[e]
                sums.sold += detail.items_sold
                sums.compensated += detail.items_compensated
                return {
                    type: "groupItem",
                    index: null,
                    description: null,
                    price: Number.parseInt(e),
                    brought: null,
                    sold: detail.items_sold,
                    compensated: detail.items_compensated,
                    returnable: null,
                }
            })
            r.unshift({
                type: "groupHead",
                index: index + 1,
                count: prices.length,
                description: item.description,
                price: null,
                brought: item.items_brought_total,
                sold: sums.sold,
                compensated: sums.compensated,
                returnable: item.items_returnable,
            })
            return r
        }
    })
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
            {rows.map((item) =>
                <BoxRows item={item} />
            )}
            {!items &&
            <tr>
                <td colSpan="6">{gettext("No boxes.")}</td>
            </tr>
            }
            {items &&
            <tr className={hideSumInPrint && "hidden-print"}>
                <th colSpan="3">{gettext("Total:")}</th>
                <th className="receipt_price numeric">{counts.brought}</th>
                <th className="receipt_price numeric">{displayPrice(sums.sold)} ({counts.sold})</th>
                <th className="receipt_price numeric"
                    style="font-weight: normal">{displayPrice(sums.compensated)} ({counts.compensated})
                </th>
                <th className="receipt_price numeric">{counts.returnable}</th>
            </tr>
            }
            </tbody>
        </table>
    )
}
