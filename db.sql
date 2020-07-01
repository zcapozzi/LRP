create table HTML_Pages
(
    ID                 bigint        null,
    page_name          varchar(100)  null,
    page_description   text          null,
    status             varchar(5000) null,
    frog_url           varchar(1000) null,
    zc_url             varchar(1000) null,
    functional_url     varchar(1000) null,
    frog_received_date datetime      null,
    zc_updated         datetime      null,
    active             tinyint       null
);

create table SVC_Adjustments
(
    project_ID          bigint       null,
    adjustment_category varchar(200) null,
    adjustment_name     varchar(200) null,
    apply               tinyint      null,
    category            varchar(150) null,
    active              tinyint      null,
    adjustment_sheet    varchar(100) null,
    ID                  bigint       null
);

create table SVC_CIM_Uploads
(
    ID              bigint        null,
    project_ID      bigint        null,
    date_received   datetime      null,
    uploader_email  varchar(1000) null,
    local_filename  varchar(1000) null,
    db_filename     varchar(1000) null,
    active          tinyint       null,
    project_name    varchar(500)  null,
    target_name     varchar(500)  null,
    target_industry varchar(500)  null
);

create table SVC_Case_Edits
(
    case_ID    bigint       null,
    category   varchar(30)  null,
    applies_to varchar(500) null,
    value      varchar(30)  null,
    active     tinyint      null,
    timestamp  bigint       null
);

create index case_update_index
    on SVC_Case_Edits (case_ID, category, applies_to);

create table SVC_Cases
(
    ID          bigint       null,
    user_ID     bigint       null,
    project_ID  bigint       null,
    active      tinyint      null,
    created_by  varchar(500) null,
    standard    tinyint      null,
    sequence    int          null,
    description text         null
);

create table SVC_Deal_Tools
(
    ID               bigint       null,
    uploaded_at      datetime     null,
    uploaded_by      varchar(500) null,
    local_file_name  text         null,
    server_file_name text         null,
    project_ID       bigint       null,
    active           tinyint      null,
    load_log         text         null,
    json_file_name   text         null
);

create table SVC_Emerging_Insights
(
    ID                    bigint        null,
    project_ID            bigint        null,
    text                  varchar(400)  null,
    sequence              int           null,
    insight_ID            bigint        null,
    url                   varchar(1000) null,
    active                tinyint       null,
    date_uploaded         datetime      null,
    new_flag              tinyint       null,
    update_flag           tinyint       null,
    category              varchar(100)  null,
    show_on_projects_page tinyint       null
);

create index active
    on SVC_Emerging_Insights (active);

create table SVC_Excel_Locations
(
    ID            bigint       null,
    file_ID       bigint       null,
    confirmed     tinyint      null,
    removed       tinyint      null,
    project_ID    bigint       null,
    location      varchar(300) null,
    location_type varchar(30)  null
);

create table SVC_Graph_Formats
(
    ID               bigint        null,
    active           tinyint       null,
    created_at       datetime      null,
    created_by       varchar(100)  null,
    original_project bigint        null,
    chart_type       varchar(50)   null,
    description      varchar(2000) null,
    raw              text          null
);

create table SVC_Hypotheses
(
    ID                     bigint       null,
    category               varchar(100) null,
    comments               text         null,
    comments_cnt           int          null,
    created_timestamp      datetime     null,
    date                   datetime     null,
    description            text         null,
    full_screen_image      tinyint      null,
    full_screen_img_ID     bigint       null,
    headline               text         null,
    headline_snippet       text         null,
    new                    tinyint      null,
    pop_out                tinyint      null,
    project_ID             bigint       null,
    selected               tinyint      null,
    sequence               int          null,
    show_on_dashboard_page tinyint      null,
    snapshot_image         tinyint      null,
    snapshot_img_ID        bigint       null,
    status                 varchar(500) null,
    subtext                text         null,
    subtext_snippet        text         null,
    tags                   text         null,
    tags_str               text         null,
    updated                tinyint      null,
    value_impact           varchar(100) null,
    value_impact_val       float        null
);

create table SVC_Image_Uploads
(
    ID               bigint        null,
    uploaded_at      datetime      null,
    uploaded_by      varchar(500)  null,
    local_file_name  varchar(1000) null,
    server_file_name varchar(1000) null,
    project_ID       bigint        null,
    active           tinyint       null,
    load_log         text          null,
    analysis_ID      bigint        null,
    image_type       varchar(50)   null,
    image_context    varchar(50)   null
);

create table SVC_Messages
(
    ID             bigint       null,
    project_ID     bigint       null,
    sequence       int          null,
    context        varchar(50)  null,
    author         varchar(100) null,
    timestamp      bigint       null,
    visible        tinyint      null,
    msg            text         null,
    author_user_ID bigint       null,
    insight_ID     bigint       null,
    analysis_ID    bigint       null,
    hypothesis_ID  bigint       null,
    new            tinyint      null,
    active         tinyint      null
);

create table SVC_Model_Files
(
    ID               bigint        null,
    uploaded_at      datetime      null,
    uploaded_by      varchar(500)  null,
    local_file_name  varchar(1000) null,
    server_file_name varchar(1000) null,
    project_ID       bigint        null,
    active           tinyint(1)    null,
    load_log         text          null,
    json_file_name   varchar(1000) null
);

create index model_file_index
    on SVC_Model_Files (ID);

create table SVC_Project_Access
(
    user_ID     bigint       null,
    project_ID  bigint       null,
    access_type varchar(100) null,
    active      tinyint(1)   null,
    is_owner    tinyint(1)   null
);

create table SVC_Projects
(
    ID                                  bigint       null,
    created_on                          datetime     null,
    created_by                          varchar(500) null,
    code_name                           text         null,
    active_file                         bigint       null,
    active                              tinyint(1)   null,
    tab_layout                          text         null,
    use_scenarios                       tinyint      null,
    use_defaults_for_sensitivity        tinyint      null,
    show_historical_data_in_graphs      tinyint      null,
    active_dealtool_file                bigint       null,
    target_name                         varchar(100) null,
    target_industry                     varchar(100) null,
    LOI_date                            datetime     null,
    phase                               varchar(20)  null,
    close_date                          datetime     null,
    stage                               varchar(50)  null,
    active_download                     text         null,
    load_from_json                      tinyint      null,
    project_group                       varchar(100) null,
    synergy_quarterly_detail            text         null,
    next_bid_date                       date         null,
    min_year                            int          null,
    qoe_period_vals1                    date         null,
    qoe_period_vals3                    date         null,
    nwc_detail_table_first_period       date         null,
    financial_overview_projection_years int          null,
    debt_like_date                      date         null
);

create table SVC_Quick_Links
(
    ID                    bigint        null,
    project_ID            bigint        null,
    text                  varchar(400)  null,
    sequence              int           null,
    analysis_ID           bigint        null,
    url                   varchar(1000) null,
    active                tinyint       null,
    date_uploaded         datetime      null,
    new_flag              tinyint       null,
    update_flag           tinyint       null,
    category              varchar(100)  null,
    show_on_projects_page tinyint       null
);

create index active
    on SVC_Quick_Links (active);

create table SVC_Sandbox_Analyses
(
    ID                    bigint       null,
    category              varchar(100) null,
    comments              text         null,
    comments_cnt          int          null,
    data_missing          tinyint      null,
    date                  datetime     null,
    full_screen_img_ID    bigint       null,
    fundamental_analysis  tinyint      null,
    headline              text         null,
    insight_ID            bigint       null,
    longtext_str          text         null,
    name                  varchar(500) null,
    new                   tinyint      null,
    phase                 varchar(100) null,
    pop_out               tinyint      null,
    project_ID            bigint       null,
    project_analysis_name varchar(500) null,
    project_code_name     varchar(500) null,
    selected              tinyint      null,
    sequence              bigint       null,
    show_on_projects_page tinyint      null,
    snapshot_img_ID       bigint       null,
    status                varchar(500) null,
    subtext               text         null,
    subtext_snippet       text         null,
    tableau_link          text         null,
    tags                  text         null,
    tags_str              text         null,
    updated               tinyint      null,
    url                   text         null,
    visible               tinyint      null
);

create table SVC_Sources
(
    ID        bigint        null,
    page      varchar(500)  null,
    sequence  int           null,
    source    text          null,
    table_loc varchar(1000) null
);

create table SVC_Status_Updates
(
    ID                    bigint        null,
    project_ID            bigint        null,
    text                  varchar(200)  null,
    sequence              int           null,
    url                   varchar(1000) null,
    active                tinyint       null,
    date_uploaded         datetime      null,
    new_flag              tinyint       null,
    update_flag           tinyint       null,
    category              varchar(100)  null,
    show_on_projects_page tinyint       null
);

create index active
    on SVC_Status_Updates (active);

create table SVC_Text_Snippets
(
    ID           bigint       null,
    element_type varchar(100) null,
    location     varchar(500) null,
    project_ID   bigint       null,
    text_str     text         null,
    value_val    text         null
);

create table SVC_Text_Sources
(
    ID        bigint        null,
    page      varchar(500)  null,
    sequence  int           null,
    source    text          null,
    table_loc varchar(1000) null
);

create table SVC_Thematic_Insights
(
    ID                           bigint        null,
    category                     varchar(500)  null,
    comments                     text          null,
    comments_cnt                 int           null,
    created_timestamp            datetime      null,
    date                         datetime      null,
    description                  text          null,
    full_screen_image            tinyint       null,
    full_screen_img_ID           bigint        null,
    hypothesis_ID                bigint        null,
    insight_ID                   bigint        null,
    name                         varchar(1000) null,
    new                          tinyint       null,
    project_ID                   bigint        null,
    selected                     tinyint       null,
    selected_thematic_insight_ID bigint        null,
    sequence                     int           null,
    show_on_dashboard_page       tinyint       null,
    snapshot_image               tinyint       null,
    snapshot_img_ID              bigint        null,
    status                       varchar(500)  null,
    subsections                  text          null,
    subtext                      text          null,
    summary                      text          null,
    summary_snippet              text          null,
    summary_snippet_long         text          null,
    tags                         text          null,
    tags_str                     text          null,
    update_flag                  tinyint       null,
    value_impact                 text          null,
    value_impact_val             float         null
);

create table SVC_User_Edits
(
    user_ID bigint null,
    edits   text   null
);

create index user_ID
    on SVC_User_Edits (user_ID);

create table SVC_Users
(
    ID                bigint       null,
    email             varchar(500) null,
    password          varchar(500) null,
    last_log_in       datetime     null,
    first_log_in      datetime     null,
    log_ins           int          null,
    active            tinyint(1)   null,
    name              text         null,
    initials          varchar(5)   null,
    is_admin          tinyint(1)   null,
    last_project      bigint       null,
    first_name        varchar(100) null,
    is_UAT            tinyint      null,
    disclaimer_agreed tinyint      null
);

