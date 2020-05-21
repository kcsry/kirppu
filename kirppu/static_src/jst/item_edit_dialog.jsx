import {Options, PriceField} from './form_fields.jsx';

function Header() {
    return (
        <div className="modal-header">
            <button className="close" data-dismiss="modal" aria-label={gettext("Close")}>
                <span aria-hidden="true">&times;</span>
            </button>
            <h4 className="modal-title">{gettext("Edit Item")}</h4>
        </div>
    )
}

function Form({CURRENCY, item_types, item_states}) {
    return (
        <form className="form-horizontal">
            <div className="form-group">
                <label htmlFor="item-edit-name-input"
                       className="col-sm-2 control-label">
                    {gettext("Name")}
                </label>
                <div className="col-sm-10">
                    <input id="item-edit-name-input"
                           type="text"
                           className="form-control"
                           readOnly/>
                </div>
            </div>
            <div className="form-group">
                <label htmlFor="item-edit-code-input"
                       className="col-sm-2 control-label">
                    {gettext("Code")}
                </label>
                <div className="col-sm-3">
                    <input id="item-edit-code-input"
                           type="text"
                           className="form-control receipt-code"
                           readOnly/>
                </div>
            </div>
            <div className="form-group">
                <label className="col-sm-2 control-label">{gettext("Vendor")}</label>
                <div id="item-edit-vendor-info" className="col-sm-10"/>
            </div>
            <div className="form-group">
                <div className="col-sm-10 col-sm-offset-2">
                    <div className="checkbox">
                        <label htmlFor="item-edit-price-confirm">
                            <input id="item-edit-price-confirm"
                                   type="checkbox"/>
                            {gettext("Vendor has requested a price change.")}
                        </label>
                    </div>
                </div>
            </div>
            <div className="form-group">
                <label htmlFor="item-edit-price-input"
                       className="col-sm-2 control-label">
                    {gettext("Price")}
                </label>
                <div className="col-sm-4">
                    <PriceField inputId="item-edit-price-input"
                        price_step="0.5" CURRENCY={CURRENCY} readOnly="true"/>
                </div>
            </div>
            <div className="form-group">
                <label htmlFor="item-edit-type-input"
                       className="col-sm-2 control-label">
                    {gettext("Type")}
                </label>
                <div className="col-sm-10">
                    <Options id="item-edit-type-input"
                             className="form-control"
                             disabled
                             list={item_types}
                    />
                </div>
            </div>
            <div className="form-group">
                <label htmlFor="item-edit-state-input"
                       className="col-sm-2 control-label">
                    State
                </label>
                <div className="col-sm-10">
                    <Options id="item-edit-state-input"
                             className="form-control"
                             list={item_states}
                    />
                </div>
            </div>
            <div className="form-group">
                <label htmlFor="item-edit-abandoned-input"
                       className="col-sm-2 control-label">
                    {gettext("Abandoned")}
                </label>
                <div className="col-sm-10">
                    <label htmlFor="item-edit-abandoned-yes"
                           className="radio-inline">
                        <input id="item-edit-abandoned-yes"
                               name="item-edit-abandoned-input"
                               type="radio"
                               value="true"
                               disabled/>
                        {gettext("Yes")}
                    </label>
                    <label htmlFor="item-edit-abandoned-no"
                           className="radio-inline">
                        <input id="item-edit-abandoned-no"
                               name="item-edit-abandoned-input"
                               type="radio"
                               value="false"
                               disabled/>
                        {gettext("No")}
                    </label>
                </div>
            </div>
        </form>
    )
}

function PrintFrame() {
    return (
        <iframe name="item-edit-print-frame" width="100%" height="100%" frameBorder="0" className="visible-print-block"
                srcDoc="
              <!doctype html>
              <html>
                <head>
                  <style>
                    button {
                      display: none !important;
                    }
                  </style>
                </head>
                <body>
                  <div id=&quot;body&quot; class=&quot;container&quot;>
                    <div id=&quot;items&quot;></div>
                  </div>
                </body>
              </html>
            "/>
    )
}


export default function render({CURRENCY, item_types, item_states}) {
    return (
        <div className="modal fade">
            <div className="modal-dialog">
                <div className="modal-content">
                    <Header/>
                    <div className="modal-body">
                        <div className="container-fluid">
                            <Form CURRENCY={CURRENCY} item_types={item_types} item_states={item_states}/>
                            <PrintFrame/>
                        </div>
                    </div>
                    <div id="item-edit-error"
                         role="alert"
                         className="alert alert-danger alert-off"/>
                    <div className="modal-footer">
                        <button className="btn btn-default btn-minwidth"
                                data-dismiss="modal">
                            {gettext("Cancel")}
                        </button>
                        <button id="item-edit-print-button"
                                className="btn btn-primary btn-minwidth">
                            {gettext("Print")}
                        </button>
                        <button id="item-edit-save-button"
                                className="btn btn-primary btn-minwidth"
                                disabled>
                            {gettext("Save")}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
