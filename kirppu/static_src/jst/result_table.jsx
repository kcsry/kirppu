export default function ResultTable({heading, head, body}) {
    return (
        <table className="table table-striped table-hover table-condensed">
            {heading && <caption className="h3">{heading}</caption>}
            {head && <thead>{head}</thead>}
            <tbody>{body}</tbody>
        </table>
    )
}
