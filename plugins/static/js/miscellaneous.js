function showMessage(msgtext, errortype) {
    let ele = $('#toast');
    let backgroundColor = errortype ? errortype == "success" ? "#efefef" : errortype == "error" ? "#efefef" : errortype == "warning" ? "#efefef" : null : null;
    let textColor = errortype == "success" ? "#0e7c7b" : errortype == "error" ? "#931621" : errortype == "warning" ? "#ffc107" : null;
    ele.text(msgtext);
    ele.css({ "color": textColor, "background-color": "#efefef", border: `1px solid ${textColor}` });
    backgroundColor && textColor ? ele.toggleClass('visible') : "";
}
let toastTimeout; // Declare a global variable to manage the timeout

function showTypeMessage(msgtext, errortype) {
    // Scroll to the top of the page
    $('html, body').animate({ scrollTop: 0 }, 'fast');
    let ele = $('.toast'); // Fix the class selector

    // Determine the background color based on the error type
    let backgroundColor = errortype ?
        errortype === "success" ? "#28a745" : // Fixed color code for success
            errortype === "error" ? "#dc3545" :
                errortype === "warning" ? "#ffc107" : null : null;

    let textColor = errortype ?
    errortype === "success" ? "#0e7c7b" : // Fixed color code for success
        errortype === "error" ? "#931621" :
            errortype === "warning" ? "#ffc107" : null : null;


    // Set text and styles
    ele.text(msgtext);
    ele.addClass("alert");
    ele.css({ "color": textColor, "background-color": "#efefef", "width": "400px", "margin": "0 auto 20px",border: `1px solid ${textColor}` });


    // Clear any existing timeout to prevent overlaps
    if (toastTimeout) {
        clearTimeout(toastTimeout);
        ele.removeClass('visible'); // Remove the class immediately to reset
    }

    // Show the toast
    if (backgroundColor && textColor) {
        ele.addClass('visible');

        // Remove the 'visible' class after a delay (e.g., 3 seconds)
        toastTimeout = setTimeout(() => {
            ele.removeClass('visible');
        }, 3000);
    }
}

function scrollAnimation(element) {
    var targetDiv = $(element);
    var scrollHeight = targetDiv.prop('scrollHeight');
    targetDiv.animate({ scrollTop: scrollHeight }, 7000);

}
function getEditsetData() {
    let workflow = $("#editData").data().set
    let workflow_json = workflow.workflow_json
    workflow.workflow_type == "parallel" ? $("#parallel_flow").prop("checked", true) : workflow.workflow_type == "series_parallel" ? $("#series_parallel_flow").prop("checked", true) : $("#series_flow").prop("checked", true)

    $("#workflow-name").val(workflow.name);
    let workflow_structure = { "drawflow": { "Home": { "data": {} } } };
    workflow_json.forEach((e) => { workflow_structure.drawflow.Home.data[e.id] = e; });
    editor.import(workflow_structure)
}

async function apiCall(data, method, url, isFormData = false) {
    let responseReturn = {}
    var csrfToken = $('meta[name=csrf-token]').attr('content');
    let ajaxOptions = {
        url: url,
        method: method,
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function (data) {
            responseReturn['responseType'] = true;
            responseReturn['data'] = data;
        },
        error: function (error) {
            responseReturn['responseType'] = false;
            responseReturn['data'] = error;
        }
    };
    if (isFormData) {
        ajaxOptions.processData = false;
        ajaxOptions.contentType = false;
        ajaxOptions.data = data;
    } else {
        ajaxOptions.contentType = "application/json";
        ajaxOptions.data = JSON.stringify(data);
    }

    await $.ajax(ajaxOptions);
    return responseReturn
}
function loading(add) {
    if (add) {
        var over = '<div id="overlay"><div class="spinner-border text-primary" role="status"></div></div>';
        $(over).appendTo('body');
    } else { $('#overlay').remove(); }

};

function buttonProgress(btn, progress) {
    if (progress) {
        let spinner = `<div class="spinner-border text-primary" role="status"></div>`
        $(btn).html(spinner)
    } else {
        $(btn + ' .spinner-border').remove();
    }
}

function saveDataLocalstorage(ele) {
    localStorage.setItem("currentWorkflowData", $(ele).data().workflow)
}

$(document).ready(() => {
    let regex = /workflow_builder\/edit\/\d+$/;
    if (regex.test(window.location.href)) { getEditsetData(); }
    $('body').on('click', '.individualChatEdit ', function () { $(this).closest('.panel-body').find(".inputContainer .chat-input-container textarea").val($(this).parent().text().trim()) })
    $("#create-workflow").click(async () => {
        //console.log(editor.export().drawflow.Home.data);
        let isParallel = checkParallelConnection(editor.export().drawflow.Home.data)
        let seriesParallel = checkSeriesParallelConnection(editor.export().drawflow.Home.data)
        let root_gpt_id
        Object.keys(editor.export().drawflow.Home.data).forEach((e) => {
            if (editor.export().drawflow.Home.data[e].outputs.output_1.connections.length) {
                root_gpt_id = editor.export().drawflow.Home.data[e].data.id
            }
        });

        if ($('#series_parallel_flow').prop("checked") && seriesParallel) {
            if ($("#workflow-name").val().trim().length) {
                if (Object.keys(editor.export().drawflow.Home.data).length) {
                    let url = window.location.href.split('/')
                    let workflow_id = url[url.length - 1];
                    let jsonArrayWorkflow = []; Object.keys(editor.export().drawflow.Home.data).forEach((e) => { jsonArrayWorkflow.push(editor.export().drawflow.Home.data[e]) })
                    // jsonArrayWorkflow.map((e)=>{return e.id = e.data.id})
                    sortOrderOfNodes.forEach((e) => {
                        const correspondingObject = jsonArrayWorkflow.find((item) => item.id === e.node);
                        if (correspondingObject) correspondingObject.sort_order = e.sortOrder;
                    });
                    loading(true)
                    let data = { "workflow_id": parseInt(workflow_id), "workflow_name": $("#workflow-name").val(), "workflow_task": JSON.stringify(jsonArrayWorkflow), "workflow_type": $("#series_parallel_flow").prop('checked') ? "series_parallel" : null, "root_gpt_id": $('#parallel_flow').prop("checked") ? root_gpt_id : null }
                    let value = await apiCall(data, 'POST', '/workflows/add_workflow');
                    setTimeout(() => {
                        loading(false)
                        if (value.responseType) {
                            if (value.data.success) {
                                showMessage(value.data.message, "success")
                                window.location.href = "/workflows";
                            } else {
                                showMessage(value.data.message, "error")
                            }
                        } else { }
                    }, 2000)
                } else { showMessage("Please choose a workflow before creating", "warning") }
            } else { showMessage("Please enter a workflow name", "warning") }
        } else if ($('#series_parallel_flow').prop("checked") && !seriesParallel) {
            showMessage("Invalid series-parallel structure", "warning")
        }
        // As both the parallel and series parallel have the same functionality, comment out this part.
        // if($('#parallel_flow').prop("checked") && isParallel){
        //     if($("#workflow-name").val().trim().length) {
        //         if(Object.keys(editor.export().drawflow.Home.data).length) {
        //             let url = window.location.href.split('/')
        //             let workflow_id = url[url.length - 1];
        //             let jsonArrayWorkflow=[]; Object.keys(editor.export().drawflow.Home.data).forEach((e)=>{jsonArrayWorkflow.push(editor.export().drawflow.Home.data[e])})
        //             // jsonArrayWorkflow.map((e)=>{return e.id = e.data.id})
        //             loading(true)
        //             let data = { "workflow_id":parseInt(workflow_id) ,"workflow_name": $("#workflow-name").val(), "workflow_task": JSON.stringify(jsonArrayWorkflow), "workflow_type" : $("#parallel_flow").prop('checked') ? "parallel" : null,"root_gpt_id":$('#parallel_flow').prop("checked") ? root_gpt_id : null}
        //             let value = await apiCall(data,'POST','/workflow/add_workflow');
        //             setTimeout(()=>{
        //                 loading(false)
        //                 if(value.responseType){
        //                     if(value.data.success){
        //                         showMessage(value.data.message, "success")
        //                         window.location.href="/workflow";
        //                     }else{
        //                         showMessage(value.data.message, "error")
        //                     }
        //                 }else{}
        //             },2000)
        //         } else {showMessage("Please choose a workflow before creating", "warning")}
        //     } else {showMessage("Please enter a workflow name", "warning")}
        // }else if($('#parallel_flow').prop("checked") && !isParallel){
        //     showMessage("Invalid parallel structure", "warning")
        // }

        if ($('#series_flow').prop("checked")) {
            let data = editor.export().drawflow.Home.data;
            if (!validateSeriesWorkflow(data)) {
                showMessage("Invalid series structure.", "warning");
                return;
            }
            if ($("#workflow-name").val().trim().length) {
                if (Object.keys(editor.export().drawflow.Home.data).length) {
                    let url = window.location.href.split('/')
                    let workflow_id = url[url.length - 1];
                    let jsonArrayWorkflow = []; //Object.keys(editor.export().drawflow.Home.data).forEach((e)=>{jsonArrayWorkflow.push(editor.export().drawflow.Home.data[e])})
                    jsonArrayWorkflow = addSortOrderForSeriesConnection(editor.export().drawflow.Home.data)
                    loading(true)
                    let data = { "workflow_id": parseInt(workflow_id), "workflow_name": $("#workflow-name").val(), "workflow_task": JSON.stringify(jsonArrayWorkflow), "workflow_type": $("#parallel_flow").prop('checked') ? "parallel" : null }
                    let value = await apiCall(data, 'POST', '/workflows/add_workflow');
                    setTimeout(() => {
                        loading(false)
                        if (value.responseType) {
                            if (value.data.success) {
                                showMessage(value.data.message, "success")
                                window.location.href = "/workflows"; // Need to redirect to the workflow list page
                            } else {
                                showMessage(value.data.message, "error")
                            }
                        } else { }
                    }, 2000)
                } else { showMessage("Please choose a workflow before creating", "warning") }
            } else { showMessage("Please enter a workflow name", "warning") }
        }

    })
    function validateSeriesWorkflow(data) {
        let nodeKeys = Object.keys(data);
        let visited = new Set();
        let currentNodeKey = nodeKeys.find(key => data[key].inputs.input_1.connections.length === 0);

        // Start from the node that has no incoming connections
        while (currentNodeKey) {
            if (visited.has(currentNodeKey)) {
                // Cycle detected
                return false;
            }

            visited.add(currentNodeKey);
            let currentNode = data[currentNodeKey];
            let outputConnections = currentNode.outputs.output_1.connections;

            if (outputConnections.length > 1) {
                // More than one outgoing connection is not allowed for series workflow
                return false;
            }

            currentNodeKey = outputConnections.length === 1 ? outputConnections[0].node : null;
        }

        // Ensure all nodes are visited, meaning all are connected in a single chain
        return visited.size === nodeKeys.length;
    }
    function addSortOrderForSeriesConnection(data) {
        let sortOrder = 1;
        let sortedNodes = [];

        // Convert the data object to an array for easier manipulation
        let nodes = Object.values(data);

        // Check if the array length is 1
        if (nodes.length === 1) {
            nodes[0].sort_order = sortOrder;
            sortedNodes.push(nodes[0]);
            return sortedNodes;
        }

        // First, find the first node
        let firstNode = nodes.find(node => node.outputs["output_1"].connections.length === 1 && node.inputs["input_1"].connections.length === 0);
        if (firstNode) {
            firstNode.sort_order = sortOrder++;
            sortedNodes.push(firstNode);
        }

        // Then, process intermediate nodes
        let currentNode = firstNode;
        while (currentNode) {
            let nextNodeId = currentNode.outputs["output_1"].connections[0]?.node;
            let nextNode = nodes.find(node => node.id == nextNodeId);
            if (nextNode && nextNode.outputs["output_1"].connections.length === 1 && nextNode.inputs["input_1"].connections.length === 1) {
                nextNode.sort_order = sortOrder++;
                sortedNodes.push(nextNode);
                currentNode = nextNode;
            } else {
                currentNode = null;
            }
        }

        // Finally, find the last node
        let lastNode = nodes.find(node => node.inputs["input_1"].connections.length === 1 && node.outputs["output_1"].connections.length === 0);
        if (lastNode) {
            lastNode.sort_order = sortOrder++;
            sortedNodes.push(lastNode);
        }

        return sortedNodes;
    }
    async function createOrEditGptType(operation) {
        let gptTypeId = $("#gpt_id").val();
        // Create a FormData object
        let formData = new FormData();
        formData.append("name", $("#gpt_name").val());
        formData.append("description", $("#gpt_description").val());
        formData.append("instruction", $("#gpt_instruction").val());
        formData.append("type", $("#gpt_type").val());

        // Get the checkbox element
        const isWebScrapeCheckbox = $("#is_web_scrape");

        // Check the checkbox state and append the value accordingly
        if (isWebScrapeCheckbox.is(":checked")) {
            formData.append("is_web_scrape", 1); // Append "1" if checked
        } else {
            formData.append("is_web_scrape", 0); // Append "0" if unchecked
        }

        // Append the file if it exists
        let fileInput = document.getElementById('gpt_file');
        if (fileInput.files.length > 0) {
            formData.append("gpt_file", fileInput.files[0]);
        }

        let url;
        if (operation === "add") {
            url = '/assistants/add_assistant';
        } else if (operation === "edit") {
            // Assuming you have the ID of the GPT type for editing
            url = `/assistants/edit_assistant/${gptTypeId}`;
        }

        let value = await apiCall(formData, 'POST', url, true);

        setTimeout(() => {
            loading(false);

            if (value.responseType) {
                if (value.data.success) {
                    showTypeMessage(value.data.message, "success");
                    setTimeout(() => {
                        window.location.href = "/assistants/";
                    }, 2000);
                } else {
                    showTypeMessage(value.data.message, "error");
                }
            } else {
                // Handle other cases if needed
            }
        }, 2000);
    }
    // Example usage for adding
    $("#create-gpt").click(async () => {
        // Get the form element
        let form = document.getElementById("gpt-form");

        // Check form validity
        if (form.checkValidity()) {
            // If the form is valid, call the createOrEditGptType function
            await createOrEditGptType("add");
        } else {
            // If the form is not valid, show validation messages
            form.reportValidity();
        }
    });


    // Example usage for editing
    $("#edit-gpt").click(async () => {
        // Get the form element
        let form = document.getElementById("gpt-form");

        // Check form validity
        if (form.checkValidity()) {
            // If the form is valid, call the createOrEditGptType function
            await createOrEditGptType("edit");
        } else {
            // If the form is not valid, show validation messages
            form.reportValidity();
        }
    });
    $(".delete-gpt").click(async function (event) {
        event.preventDefault(); // Prevent the default behavior of the link

        // Get the GPT ID from the data attribute
        var gptId = $(this).data("gpt-id");
        console.log("gptId", gptId);

        // Check if the GPT exists in any workflow using AJAX
        $.ajax({
            url: '/assistants/check_gpt_exist_workflow/' + gptId,
            method: 'GET',
            success: function (response) {
                if (response.success === false) {
                    // Handle the case where the GPT is used in workflows
                    window.scrollTo(0, 0);
                    let workflowsMessage = response.workflows && response.workflows.length > 0
                        ? `\n- ${response.workflows.join('\n, ')}`
                        : '';

                    let fullMessage = `${response.message}${workflowsMessage}`;
                    showTypeMessage(fullMessage, "error");
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    // Proceed with showing the confirmation modal
                    $("#deleteConfirmationModal").modal("show");

                    // Set up the confirm button with the appropriate action
                    $("#deleteConfirmButton").off("click").on("click", async function () {
                        // Perform the DELETE request using the apiCall function
                        try {
                            let value = await apiCall({}, 'POST', '/assistants/delete_gpt/' + gptId);

                            // Handle the response after the DELETE request
                            loading(false);
                            setTimeout(() => {
                                loading(false);

                                if (value.responseType) {
                                    if (value.data.success) {
                                        window.scrollTo(0, 0);
                                        showTypeMessage(value.data.message, "success");
                                        setTimeout(() => {
                                            window.location.reload();
                                        }, 2000);
                                    } else {
                                        window.scrollTo(0, 0);
                                        let fullMessage = `${value.data.message}`;
                                        showTypeMessage(fullMessage, "error");
                                        setTimeout(() => {
                                            window.location.reload();
                                        }, 2000);
                                    }
                                }
                            }, 2000);
                        } catch (error) {
                            console.error("Error:", error);
                            showTypeMessage("An error occurred", "error");
                            setTimeout(() => {
                                window.location.reload();
                            }, 500);
                        }

                        // Hide the modal after confirming
                        $("#deleteConfirmationModal").modal("hide");
                    });
                }
            },
            error: function (error) {
                console.error("Error checking GPT workflow existence:", error);
                showTypeMessage("An error occurred while checking workflow existence", "error");
            }
        });
    });
});
function checkParallelConnection(data) {
    // Find the node with an input of 0 and output of (length of keys - 1)
    let zeroInputNode = null;
    let outputLengthMinusOneNode = null;

    for (const key in data) {
        const node = data[key];
        const inputKeys = Object.keys(node.inputs);

        if (inputKeys.length === 1 && inputKeys[0] === "input_1" && node.inputs["input_1"].connections.length === 0) {
            zeroInputNode = node;
        }
        // check all inputs are connected as per parallel connection
        if (Object.keys(node.outputs.output_1.connections).length === Object.keys(data).length - 1) {
            let allOutputsConnected = true;
            // find the end node and break the function
            for (const outputKey in node.outputs) {
                if (node.outputs[outputKey].connections.length === 0) {
                    allOutputsConnected = false;
                    break;
                }
            }
            if (allOutputsConnected) {
                outputLengthMinusOneNode = node;
            }
        }

        if (zeroInputNode && outputLengthMinusOneNode) {
            break;
        }
    }

    // Check if conditions are met
    if (zeroInputNode && outputLengthMinusOneNode) {
        // Set zero input node's output to outputLengthMinusOneNode
        zeroInputNode.outputs.output_1.connections.push({
            node: outputLengthMinusOneNode.id.toString(),
            output: "input_1"
        });

        // Set other nodes' outputs to zero input node
        for (const key in data) {
            const node = data[key];
            if (node !== zeroInputNode && node.outputs.output_1) {
                node.outputs.output_1.connections = [{
                    node: zeroInputNode.id.toString(),
                    output: "input_1"
                }];
            }
        }

        // console.log("Success: Conditions met. Connections updated successfully.");
        return true
    } else {
        return false
        // console.error("Error: Conditions not met. Unable to update connections.");
    }
}


function checkSeriesParallelConnection(data) {
    // Find the node with an input of 0 and output of (length of keys - 1)
    let zeroInputNode = null;
    let lastSeriesNode = {};
    let seriesToParallelNode = null;
    let isSeriesParallel = false
    sortOrderOfNodes = []

    for (const key in data) {
        const node = data[key];
        const inputKeys = Object.keys(node.inputs);
        if (inputKeys.length === 1 && inputKeys[0] === "input_1" && node.inputs["input_1"].connections.length === 0) {
            zeroInputNode = node;
            let obj = {}
            obj["sortOrder"] = 1;
            obj["node"] = node.id;
            sortOrderOfNodes.push(obj);
        }
        const outputKeys = Object.keys(node.outputs);
        if (outputKeys.length === 1 && outputKeys[0] === "output_1" && node.outputs["output_1"].connections.length > 1) {
            seriesToParallelNode = node
            let isEnd = [];
            if (node.outputs["output_1"].connections.every(gpt => data[gpt.node].outputs["output_1"].connections.length === 0)) {
                node.outputs["output_1"].connections.forEach(gpt => {
                    const hasSortOrder = sortOrderOfNodes.some(item => {
                        return item.sortOrder === Object.keys(data).length - 2;
                    });
                    if (!hasSortOrder) {
                        lastSeriesNode["sortOrder"] = Object.keys(data).length - 2;
                        lastSeriesNode["node"] = node.id;
                        sortOrderOfNodes.push(lastSeriesNode);
                    }
                    let obj = {}
                    obj["sortOrder"] = Object.keys(data).length - 1;
                    obj["node"] = data[gpt.node].id;
                    sortOrderOfNodes.push(obj);
                    isEnd.push(data[gpt.node]);
                });
            }
            if (isEnd.length == 0) {
                isSeriesParallel = false;
                return
            } else {
                isSeriesParallel = true;
            }

        }
    }
    if (zeroInputNode) {
        for (const key in data) {
            let checkNode = data[key]
            if (checkNode.outputs["output_1"].connections.length == 1 && checkNode.inputs["input_1"].connections.length == 1) {
                if (zeroInputNode.id == checkNode.inputs["input_1"].connections[0].node) {
                    let x = 1
                    let obj = {
                        "sortOrder": x + 1,
                        "node": checkNode.id
                    }
                    sortOrderOfNodes.push(obj);
                }
            }
        }
    }
    return isSeriesParallel
}
document.addEventListener('DOMContentLoaded', function () {
    var gptTypeSelect = document.getElementById('gpt_type');
    var uploadRow = document.getElementById('upload-row');
    var uploadBtn = document.getElementById('upload-btn');
    var fileInput = document.getElementById('gpt_file');
    var fileNameStatus = document.getElementById('file-name-status');

    gptTypeSelect.addEventListener('change', function () {
        if (gptTypeSelect.value === 'ASSISTANT') {
            uploadRow.classList.remove('hidden');
        } else {
            uploadRow.classList.add('hidden');
        }
    });

    // Trigger the change event on page load to set the initial state
    gptTypeSelect.dispatchEvent(new Event('change'));

    uploadBtn.addEventListener('click', function () {
        fileInput.click();
    });

    fileInput.addEventListener('change', function () {
        if (fileInput.files.length > 0) {
            var fileName = fileInput.files[0].name;
            fileNameStatus.innerHTML = `File "${fileName}" uploaded successfully.`;
            fileNameStatus.style.color = 'green';
        } else {
            fileNameStatus.innerHTML = '';
        }
    });
});
// Function to handle pagination and fetch user list
function handlePagination(pageNumber) {
    var selectedGptIds = getSelectedGptIds();
    var searchQuery = $("#modal-search-input").val();
    var gptSearchString = "gpt_ids=" + selectedGptIds.join('&gpt_ids=');
    var queryString = $.param({
        modal_search: searchQuery,
        modal_page: pageNumber,
        modal_per_page: 10  // Assuming 10 items per page
    });
    fetchUserList('/assistants/list_gpt_access?' + queryString + '&' + gptSearchString);
}
// Function to fetch user list via AJAX
function fetchUserList(url) {
    let urlParams = new URLSearchParams(url.split('?')[1]);
        let isSearch = urlParams.has('modal_search') && urlParams.get('modal_search').trim() !== "" ? true : false;
        let searchVal = isSearch ?   urlParams.get('modal_search').trim() : "";
    $.ajax({
        url: url,
        method: 'GET',
        success: function (response) {
            if (response.success) {
                var tableBody = $("#access-control-modal table tbody");
                tableBody.empty(); // Clear existing rows

                // response.data.forEach(function(user) {
                //     var row = '<tr>' +
                //         '<td><input type="checkbox" class="user-checkbox" data-user-id="' + user.user_id + '" ' + (user.is_enabled ? 'checked' : '') + '></td>' +
                //         '<td>' + user.first_name +' '+ user.last_name + '</td>' +
                //         '<td>' + user.email + '</td>' +
                //         '</tr>';
                //     tableBody.append(row);
                // });

                if (response && response.is_parent_child == 0) {
                    let resData = response.data[0].clients;
                    resData.forEach(function (user) {
                        // Create the main row for the user without a checkbox
                        var row = '<tr>' +
                            '<td><input type="checkbox" class="client-checkbox" data-client-id="' + user.user_id + '" ' + (user.is_enabled ? 'checked' : '') + '></td>' +
                            '<td>' + user.first_name + ' ' + user.last_name + '</td>' +
                            '<td>' + user.email + '</td>' +
                            // Add button for toggling clients section
                            //  '<td><button class="custom_butt_col btn btn-primary toggle-clients" type="button" data-toggle="collapse" data-target="#clients-' + user.user_id + '" aria-expanded="false">Show Users</button></td>' +
                            '</tr>';



                        // Append both the user row and the clients row to the table
                        tableBody.append(row);
                        //  tableBody.append(clientsRow);
                    });

                } else {

                    response.data.forEach(function (user) {
                        let isMatchFound;
                        if(isSearch){
                            isMatchFound = user.clients.some(function (user) {
                                return user.first_name.includes(searchVal) || user.email.includes(searchVal);
                            });

                        }
                        let ariaExpand = isSearch && isMatchFound ? 'true' :"false";
                        let buttonText = isSearch && isMatchFound ? 'Hide Users' :'Show Users';
                        let customCollapClass =isSearch && isMatchFound ? " collapse in" :" collapse"
                        // Create the main row for the user without a checkbox
                        var row = '<tr>' +
                            '<td><input type="checkbox" class="client-checkbox" data-client-id="' + user.user_id + '" ' + (user.is_enabled ? 'checked' : '') + '></td>' +
                            '<td>' + user.first_name + ' ' + user.last_name + '</td>' +
                            '<td>' + user.email + '</td>' +
                            // Add button for toggling clients section
                            '<td><button class="custom_butt_col btn btn-primary toggle-clients" type="button" data-toggle="collapse" data-target="#clients-' + user.user_id + '" aria-expanded="'+ariaExpand+'">'+buttonText+'</button></td>' +
                            '</tr>';

                        // Create the hidden row for the clients (accordion)
                        var clientsRow = '<tr class="'+customCollapClass+'" id="clients-' + user.user_id + '">' +
                            '<td colspan="5">';

                        // Check if clients array is empty
                        if (user.clients.length === 0) {
                            // If no clients, show a "No clients" message centered
                            clientsRow += '<div style="text-align: center;">No Users</div>';
                        } else {
                            // Add a table with headers for the clients
                            clientsRow += '<table class="table table-bordered">' +
                                '<thead><tr>' +
                                '<th><input type="checkbox" class="select-all"></th>' +  // "Select All" checkbox in the first column
                                '<th>First Name</th>' +
                                '<th>Email</th>' +
                                '</tr></thead>' +
                                '<tbody>';

                            // Add each client with a checkbox and two fields (first_name, email)
                            user.clients.forEach(function (client) {
                                clientsRow += '<tr>' +
                                    '<td><input type="checkbox" class="client-checkbox" data-client-id="' + client.user_id + '"  ' + (client.is_enabled ? 'checked' : '') + '></td>' +  // Checkbox for each client
                                    '<td>' + client.first_name + '</td>' +
                                    '<td>' + client.email + '</td>' +
                                    '</tr>';
                            });

                            clientsRow += '</tbody></table>';
                        }

                        clientsRow += '</td></tr>';

                        // Append both the user row and the clients row to the table
                        tableBody.append(row);
                        tableBody.append(clientsRow);
                    });

                    var userData = [];
                    const submitButton = document.getElementById('update-access');

                    // Initially disable the button
                    submitButton.disabled = true;

                    // Store initial states of checkboxes
                    const initialStates = $(".client-checkbox").map(function () {
                        return $(this).prop("checked");
                    }).get();

                    // Function to check if any checkbox state has changed
                    function updateButtonState() {
                        const hasChanged = $(".client-checkbox").toArray().some((checkbox, index) => {
                            return $(checkbox).prop("checked") !== initialStates[index];
                        });
                        submitButton.disabled = !hasChanged;
                    }

                    // Monitor each checkbox for changes
                    
                    $(".client-checkbox").on("change", function () {
                        updateButtonState();

                        // Update userData array with the current state of each checkbox
                        userData = $(".client-checkbox").map(function () {
                            return {
                                "user_id": $(this).data("client-id"),
                                "is_enabled": $(this).prop("checked") ? 1 : 0
                            };
                        }).get();
                    });

                }




                // Ensure the modal is displayed after fetching data
                var modal = document.getElementById("access-control-modal");
                modal.style.display = "block";
                updatePagination(response);
            } else {
                showTypeMessage("Failed to fetch user access data", "error");
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log("Error:", jqXHR.responseText);
            showTypeMessage("An error occurred while fetching user access data", "error");
        }
    });
}
// Function to update pagination controls
function updatePagination(response) {
    var pagination = $('#modal_pagination');
    pagination.empty();
    var totalPages = Math.ceil(response.modal_total / response.modal_per_page);
    var currentPage = response.modal_page;

    if (totalPages > 1) {
        if (currentPage > 1) {
            pagination.append('<li class="page-item"><a class="page-link modal-pagination-link" href="#" data-page="' + (currentPage - 1) + '">&laquo;</a></li>');
        }

        for (var i = 1; i <= totalPages; i++) {
            var activeClass = (i === currentPage) ? 'active' : '';
            pagination.append('<li class="page-item ' + activeClass + '"><a class="page-link modal-pagination-link" href="#" data-page="' + i + '">' + i + '</a></li>');
        }

        if (currentPage < totalPages) {
            pagination.append('<li class="page-item"><a class="page-link modal-pagination-link" href="#" data-page="' + (currentPage + 1) + '">&raquo;</a></li>');
        }
    }
}
// Function to get selected GPT IDs
function getSelectedGptIds() {
    var selectedGptIds = [];
    $(".gpt-radio:checked").each(function () {
        selectedGptIds.push($(this).data("gpt-id"));
    });
    return selectedGptIds;
}

// JavaScript for Access Control Popup
$(document).ready(function () {



    // Event listener for toggling the button text
    $(document).on('click', '.toggle-clients', function () {
        var button = $(this);
        var isExpanded = button.text() === 'Show Users';

        // Toggle button text between "Show Users" and "Hide Users"
        if (isExpanded) {
            button.text('Hide Users');
        } else {
            button.text('Show Users');
        }
    });

    // Event listener for the "Select All" checkbox
    $(document).on('click', '.select-all', function () {
        var isChecked = $(this).prop('checked');
        $(this).closest('table').find('.client-checkbox').prop('checked', isChecked);
    });

    // Get the modal
    var modal = document.getElementById("access-control-modal");

    // Get the button that opens the modal
    var btn = document.getElementById("access-control-button");

    // Get the <span> element that closes the modal
    //var span = document.getElementsByClassName("access-control-modal-close");

    // When the user clicks the button, open the modal 
    $("#access-control-button").on("click", function () {
        // Refresh the selected GPT IDs each time the button is clicked
        var selectedGptIds = getSelectedGptIds();

        // Check if any GPT is selected
        if (selectedGptIds.length === 0) {
            showTypeMessage("Please select GPT", "error");
            setTimeout(() => {
                window.location.href = "/assistants/";
            }, 2000);
        }
        else {
            // Manually construct the query string
            handlePagination(1); // Start from page 1
        }
    });
    // Handle pagination clicks in the main table
    $(document).on("click", "#main-pagination-link", function (event) {
        event.preventDefault();
        window.location.href = $(this).attr('href');
    });
    // Handle pagination clicks in the modal
    $(document).on("click", ".modal-pagination-link", function (event) {
        event.preventDefault();
        var page = $(this).data("page");
        handlePagination(page);
    });
    // When the user clicks on <span> (x), close the modal
    // // Get the close button
    const closeButton = document.querySelector(".access-control-modal-content .close");

    // When the user clicks on <span> (x), close the modal
    closeButton.addEventListener("click", function () {
        modal.style.display = "none";
    });
    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };

    // Prevent form submission and modal close on Enter key press
    $("#modal-search-form").on("submit", function (event) {
        event.preventDefault();
        handlePagination(1); // Start from page 1
    });
    // Add on-key search functionality
    $("#modal-search-input").on("input", function () {
        handlePagination(1); // Start from page 1 on input change
    });
    // Handle pagination clicks in the modal
    $(document).on("click", ".modal-pagination", function (event) {
        event.preventDefault();
        var page = $(this).data("page");
        var searchQuery = $("#modal-search-input").val();
        var queryString = $.param({
            modal_search: searchQuery,
            modal_page: page
        });
        $.ajax({
            url: '/assistants/list_gpt_access?' + queryString,
            method: 'GET',
            success: function (response) {
                if (response.success) {
                    $(".user-checkbox").prop("checked", false);
                    response.data.forEach(function (item) {
                        if (item.is_enabled === 1) {
                            $(".user-checkbox[data-user-id='" + item.user_id + "']").prop("checked", true);
                        }
                    });
                    modal.style.display = "block";
                } else {
                    showTypeMessage("Failed to fetch user access data", "error");
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.log("Error:", jqXHR.responseText);
                showTypeMessage("An error occurred while fetching user access data", "error");
            }
        });
    });
    // Handle form submission
    $("#update-access").on("click", function () {
        var selectedGptIds = [];
        $(".gpt-radio:checked").each(function () {
            selectedGptIds.push($(this).data("gpt-id"));
        });

        var userData = [];
        $(".client-checkbox").each(function () {
            var userId = $(this).data("client-id");
            var isEnabled = $(this).prop("checked") ? 1 : 0;

            userData.push({
                "user_id": userId,
                "is_enabled": isEnabled
            });
        });

        var data = {
            user_data: userData,
            gpt_ids: selectedGptIds
        };

        $.ajax({
            url: "/assistants/add_gpt_access",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(data),
            headers: {
                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
            },
            success: function (response) {
                if (response.requires_confirmation) {
                    // Show confirmation popup
                    $("#accessConfirmationModal").modal("show");

                    // Handle confirmation
                    $("#accessConfirmButton").off("click").on("click", function () {
                        data.confirmation = true;
                        $.ajax({
                            url: "/assistants/add_gpt_access",
                            method: "POST",
                            contentType: "application/json",
                            data: JSON.stringify(data),
                            headers: {
                                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
                            },
                            success: function (res) {
                                showTypeMessage("Access updated successfully", "success");
                                setTimeout(function () {
                                    window.location.href = "/assistants/";
                                }, 2000);
                            },
                            error: function (jqXHR, textStatus, errorThrown) {
                                console.error("An error occurred: " + jqXHR.responseText);
                                showTypeMessage("Access not updated successfully", "error");
                                setTimeout(function () {
                                    window.location.href = "/assistants/";
                                }, 2000);
                            }
                        });
                        $("#accessConfirmationModal").modal("hide"); // Hide the modal after confirmation
                    });
                } else {
                    showTypeMessage("Access updated successfully", "success");
                    var modal = document.getElementById("access-control-modal"); modal.style.display = "none";
                    setTimeout(function () {
                        window.location.href = "/assistants/";
                    }, 2000);
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("An error occurred: " + jqXHR.responseText);
                showTypeMessage("Access not updated successfully", "error");
                setTimeout(function () {
                    window.location.href = "/assistants/";
                }, 2000);
            }
        });
    });

    // Ensure modal is hidden when clicking outside or pressing escape
    $("#accessConfirmationModal").on('hidden.bs.modal', function () {
        // Remove dark backdrop if it remains
        $('.modal-backdrop').remove();
    });


    // Select All checkboxes in GPT table
    // $("#select-all-gpt").on("change", function(){
    //     $(".gpt-checkbox").prop("checked", $(this).prop("checked"));
    // });

    // Select All checkboxes in User table
    $("#select-all-users").on("change", function () {
        $(".user-checkbox").prop("checked", $(this).prop("checked"));
    });

    // Check if any checkbox is unchecked in GPT table
    // $(".gpt-checkbox").on("change", function(){
    //     if (!$(this).prop("checked")) {
    //         $("#select-all-gpt").prop("checked", false);
    //     }
    // });

    // Check if any checkbox is unchecked in User table
    $(".user-checkbox").on("change", function () {
        if (!$(this).prop("checked")) {
            $("#select-all-users").prop("checked", false);
        }
    });

});
$(document).ready(function () {
    $("#add_user").click(async () => {
        // Get the form element
        let form = document.getElementById("model_form");

        // Check form validity
        if (form.checkValidity()) {
            // If the form is valid, call the createOrEditGptType function
            await addOrEditUser("add");
        } else {
            // If the form is not valid, show validation messages
            form.reportValidity();
        }
    });
    $("#edit_user").click(async () => {
        // Get the form element
        let form = document.getElementById("model_form");

        // Check form validity
        if (form.checkValidity()) {
            // If the form is valid, call the createOrEditGptType function
            await addOrEditUser("edit");
        } else {
            // If the form is not valid, show validation messages
            form.reportValidity();
        }
    });
    async function addOrEditUser(operation) {
        let user_id = $("#user_id").val();
        // Create a FormData object
        let formData = new FormData();
        let is_active = $("#is_active").is(":checked");  // true if checked, false otherwise
        formData.append("first_name", $("#first_name").val());
        formData.append("last_name", $("#last_name").val());
        formData.append("username", $("#username").val());
        formData.append("is_active", is_active);
        formData.append("email", $("#email").val());
        formData.append("role", $("#role").val());
        var userLimit = $("#user_limit").val();
        if (userLimit && userLimit !== undefined) {
            formData.append("user_limit", userLimit !== undefined ? userLimit : null);
        }

        let url;
        if (operation === "add") {
            formData.append("password", $("#password").val());
            formData.append("confirm_password", $("#confirm_password").val());
            url = '/user_management/add_user';
        }
        else if (operation === "edit") {
            url = `/user_management/edit_user/${user_id}`;
        }

        let value = await apiCall(formData, 'POST', url, true);

        setTimeout(() => {
            loading(false);

            if (value.responseType) {
                if (value.data.success) {
                    showTypeMessage(value.data.message, "success");
                    setTimeout(() => {
                        window.location.href = "/user_management/";
                    }, 2000);
                } else {
                    showTypeMessage(value.data.message, "error");
                }
            } else {
                // Handle other cases if needed
            }
        }, 2000);
    }
    function goBack() {
        window.history.back();
    }
    $(".goBack").on("click", function (event) {
        event.preventDefault();  // Prevent the default anchor behavior
        goBack();
    });


    $(".assign_workflow").on("click", async function () {
        var workflow_id = $(this).data("workflow_id");
        // Assign workflow_id to the Update Access button
        $("#update-user-workflow-access").data("workflow_id", workflow_id);
        fetchWorkflowUserList('/user_management/list_workflow_access?workflow_id=' + workflow_id);
    });
    function fetchWorkflowUserList(url) {
        let urlParams = new URLSearchParams(url.split('?')[1]);
        let isSearch = urlParams.has('modal_search') && urlParams.get('modal_search').trim() !== "" ? true : false;
        let searchVal = isSearch ?   urlParams.get('modal_search').trim() : "";
        $.ajax({
            url: url,
            method: 'GET',
            success: function (response) {
                if (response.success) {
                    var tableBody = $("#workflow-access-control-modal table tbody");
                    tableBody.empty(); // Clear existing rows
                    if (response && response.is_parent_child == 0) {
                        let resData = response.data[0].clients;
                        resData.forEach(function (user) {
                            // Create the main row for the user without a checkbox
                            var row = '<tr>' +
                                '<td><input type="checkbox" class="client-checkbox" data-client-id="' + user.user_id + '" ' + (user.is_enabled ? 'checked' : '') + '></td>' +
                                '<td>' + user.first_name + ' ' + user.last_name + '</td>' +
                                '<td>' + user.email + '</td>' +
                                '</tr>';
                            // Append both the user row and the clients row to the table
                            tableBody.append(row);
                        });

                    } else {
                        response.data.forEach(function (user) {
                            let isMatchFound;
                            if(isSearch){
                                isMatchFound = user.clients.some(function (user) {
                                    return user.first_name.includes(searchVal) || user.email.includes(searchVal);
                                });

                            }
                            // Check if any object's first_name or email contains the searchString
                            // Create the main row for the user without a checkbox
                            let ariaExpand = isSearch && isMatchFound ? 'true' :"false";
                            let buttonText = isSearch && isMatchFound ? 'Hide Users' :'Show Users';
                            let customCollapClass =isSearch && isMatchFound ? " collapse in" :" collapse"
                            var row = '<tr>' +
                                '<td><input type="checkbox" class="client-checkbox" data-client-id="' + user.user_id + '" ' + (user.is_enabled ? 'checked' : '') + '></td>' +
                                '<td>' + user.first_name + ' ' + user.last_name + '</td>' +
                                '<td>' + user.email + '</td>' +
                                // Add button for toggling clients section
                                '<td><button class="custom_butt_col btn btn-primary toggle-clients" type="button" data-toggle="collapse" data-target="#clients-' + user.user_id + '" aria-expanded="'+ariaExpand+'">'+buttonText+'</button></td>' +
                                '</tr>';

                            // Create the hidden row for the clients (accordion)
                            var clientsRow = '<tr class="'+customCollapClass+'" aria-expanded="'+ariaExpand+'" id="clients-' + user.user_id + '">' +
                                '<td colspan="5">';

                            // Check if clients array is empty
                            if (user.clients.length === 0) {
                                // If no clients, show a "No clients" message centered
                                clientsRow += '<div style="text-align: center;">No Users</div>';
                            } else {
                                // Add a table with headers for the clients
                                clientsRow += '<table class="table table-bordered">' +
                                    '<thead><tr>' +
                                    '<th><input type="checkbox" class="select-all"></th>' +  // "Select All" checkbox in the first column
                                    '<th>First Name</th>' +
                                    '<th>Email</th>' +
                                    '</tr></thead>' +
                                    '<tbody>';

                                // Add each client with a checkbox and two fields (first_name, email)
                                user.clients.forEach(function (client) {
                                    clientsRow += '<tr>' +
                                        '<td><input type="checkbox" class="client-checkbox" data-client-id="' + client.user_id + '"  ' + (client.is_enabled ? 'checked' : '') + '></td>' +  // Checkbox for each client
                                        '<td>' + client.first_name + '</td>' +
                                        '<td>' + client.email + '</td>' +
                                        '</tr>';
                                });

                                clientsRow += '</tbody></table>';
                            }

                            clientsRow += '</td></tr>';

                            // Append both the user row and the clients row to the table
                            tableBody.append(row);
                            tableBody.append(clientsRow);
                        });
                        var userData = [];
                        const submitButton = document.getElementById('update-user-workflow-access');

                        // Initially disable the button
                        submitButton.disabled = true;

                        // Store initial states of checkboxes
                        const initialStates = $(".client-checkbox").map(function () {
                            return $(this).prop("checked");
                        }).get();

                        // Function to check if any checkbox state has changed
                        function updateButtonState() {
                            const hasChanged = $(".client-checkbox").toArray().some((checkbox, index) => {
                                return $(checkbox).prop("checked") !== initialStates[index];
                            });
                            submitButton.disabled = !hasChanged;
                        }

                        // Monitor each checkbox for changes
                        
                        $(".client-checkbox").on("change", function () {
                            updateButtonState();

                            // Update userData array with the current state of each checkbox
                            userData = $(".client-checkbox").map(function () {
                                return {
                                    "user_id": $(this).data("client-id"),
                                    "is_enabled": $(this).prop("checked") ? 1 : 0
                                };
                            }).get();
                        });
                    }



                    // Ensure the modal is displayed after fetching data
                    var modal = document.getElementById("workflow-access-control-modal");
                    modal.style.display = "block";
                    updateWorkFlowUserPagination(response);
                } else {
                    showTypeMessage("Failed to fetch workflow user access data", "error");
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                showTypeMessage("An error occurred while fetching workflow user access data", "error");
            }
        });
    }
    function updateWorkFlowUserPagination(response) {
        var pagination = $('#workflow_user_modal_pagination');
        pagination.empty();
        var totalPages = Math.ceil(response.modal_total / response.modal_per_page);
        var currentPage = response.modal_page;

        if (totalPages > 1) {
            if (currentPage > 1) {
                pagination.append('<li class="page-item"><a class="page-link workflow-modal-pagination-link" href="#" data-page="' + (currentPage - 1) + '">&laquo;</a></li>');
            }

            for (var i = 1; i <= totalPages; i++) {
                var activeClass = (i === currentPage) ? 'active' : '';
                pagination.append('<li class="page-item ' + activeClass + '"><a class="page-link workflow-modal-pagination-link" href="#" data-page="' + i + '">' + i + '</a></li>');
            }

            if (currentPage < totalPages) {
                pagination.append('<li class="page-item"><a class="page-link workflow-modal-pagination-link" href="#" data-page="' + (currentPage + 1) + '">&raquo;</a></li>');
            }
        }
    }
    // // Get the modal
    var modal = document.getElementById("workflow-access-control-modal");

    // // Get the close button
    const closeButton = document.querySelector(".workflow-access-modal-content .close");

    // When the user clicks on <span> (x), close the modal
    closeButton.addEventListener("click", function () {
        modal.style.display = "none";
    });

    // // When the user clicks anywhere outside of the modal, close it
    window.addEventListener("click", function (event) {

        if (event.target == modal) {
            modal.style.display = "none";
        }
    });
    // Handle form submission
    $("#update-user-workflow-access").on("click", function () {
        var workflow_id = $(this).data("workflow_id");
        var userData = [];
        $(".client-checkbox").each(function () {
            var userId = $(this).data("client-id");
            var isEnabled = $(this).prop("checked") ? 1 : 0;

            userData.push({
                "user_id": userId,
                "is_enabled": isEnabled
            });
        });

        var data = {
            user_data: userData,
            workflow_id: workflow_id
        };

        // Send selected user IDs and Workflows to the server
        $.ajax({
            url: "/user_management/add_workflow_access",  // Update this URL to your actual endpoint
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(data),
            headers: {
                'X-CSRFToken': csrfToken  // Ensure csrfToken is defined somewhere in your script
            },
            success: function (response) {
                var modal = document.getElementById("workflow-access-control-modal");
                modal.style.display = "none";
                showTypeMessage("Access updated successfully", "success");
                setTimeout(() => {
                    window.location.href = "/workflows/";
                }, 2000);
            },
            error: function (jqXHR, textStatus, errorThrown) {
                var modal = document.getElementById("workflow-access-control-modal");
                modal.style.display = "none";
                showTypeMessage("Access not updated successfully", "error");
                setTimeout(() => {
                    window.location.href = "/workflows/";
                }, 2000);
            }
        });
    });
    // Handle pagination clicks in the modal
    $(document).on("click", ".workflow-modal-pagination-link", function (event) {
        event.preventDefault();
        var page = $(this).data("page");
        handleWorkflowPagination(page);
    });
    // Prevent form submission and modal close on Enter key press
    $("#modal-workflow-search-form").on("submit", function (event) {
        event.preventDefault();
        handleWorkflowPagination(1); // Start from page 1
    });
    // Add on-key search functionality
    $("#modal-workflow-search-input").on("input", function () {
        handleWorkflowPagination(1); // Start from page 1 on input change
    });
    // Handle pagination clicks in the modal
    $(document).on("click", ".workflow-modal-pagination", function (event) {
        event.preventDefault();
        var page = $(this).data("page");
        var searchQuery = $("#modal-workflow-search-input").val();
        var queryString = $.param({
            modal_search: searchQuery,
            modal_page: page
        });
        $.ajax({
            url: '/user_management/list_workflow_access?' + queryString,
            method: 'GET',
            success: function (response) {
                if (response.success) {
                    $(".user-checkbox").prop("checked", false);
                    response.data.forEach(function (item) {
                        if (item.is_enabled === 1) {
                            $(".user-checkbox[data-user-id='" + item.user_id + "']").prop("checked", true);
                        }
                    });
                    modal.style.display = "block";
                } else {
                    showTypeMessage("Failed to fetch user access data", "error");
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.log("Error:", jqXHR.responseText);
                showTypeMessage("An error occurred while fetching user access data", "error");
            }
        });
    });
    // Function to handle pagination and fetch user list
    function handleWorkflowPagination(pageNumber) {
        var workflow_id = $("#update-user-workflow-access").data("workflow_id");
        var searchQuery = $("#modal-workflow-search-input").val();
        var gptSearchString = "workflow_id=" + workflow_id;
        var queryString = $.param({
            modal_search: searchQuery,
            modal_page: pageNumber,
            modal_per_page: 10  // Assuming 10 items per page
        });
        fetchWorkflowUserList('/user_management/list_workflow_access?' + queryString + '&' + gptSearchString);
    }
});


$(document).on("click", ".delete_user", async function (event) {
    event.preventDefault(); // Prevent the default behavior of the link

    var user_id = $(this).data("user_id");
    // Store user_id in the confirm button data attribute for later use
    $("#confirmDeleteButton").data("user_id", user_id);

    // Show the modal
    $("#deleteUserModal").modal("show");



    // Handle the confirm delete button click
    $("#confirmDeleteButton").on("click", async function () {
        var user_id = $(this).data("user_id"); // Retrieve user_id stored in the button data attribute
        // Hide the modal after confirming
        $("#deleteUserModal").modal("hide");
        try {
            // Perform the DELETE request using the apiCall function
            let value = await apiCall({}, 'POST', '/user_management/delete_user/' + user_id);

            // Handle the response after the DELETE request
            loading(false);
            setTimeout(() => {
                loading(false);

                if (value.responseType) {
                    if (value.data.success) {
                        window.scrollTo(0, 0);
                        showTypeMessage(value.data.message, "success");
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    } else {
                        window.scrollTo(0, 0);
                        showTypeMessage(value.data.message, "error");
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    }
                } else {
                    // Handle other cases if needed
                }
            }, 2000);
        } catch (error) {
            console.error("Error:", error);
            showTypeMessage("An error occurred", "error");
            setTimeout(() => {
                window.location.reload();
            }, 500);
        }

    });
});
$(document).ready(function () {

    async function createOrEditClientAdmin(operation) {
        let clientAdminId = $("#clientadmin_id").val();

        // Create a FormData object
        let formData = new FormData();
        formData.append("firstname", $("#firstname").val());
        formData.append("lastname", $("#lastname").val());
        formData.append("username", $("#username").val());
        formData.append("email", $("#email").val());
        formData.append("password", $("#password").val());
        formData.append("confirmpassword", $("#confirmpassword").val());
        formData.append("userlimit", $("#userlimit").val());

        // Get the checkbox element
        const active = $("#active");

        // Check the checkbox state and append the value accordingly
        if (active.is(":checked")) {
            formData.append("active", "true");
        } else {
            formData.append("active", "false");
        }
        let userLimitValue = parseInt($("#userlimit").val(), 10);
        formData.append("user_limit", userLimitValue);
        let url;
        if (operation === "add") {
            url = '/clientadmin/add_client';
        } else if (operation === "edit") {
            // Assuming you have the ID of the GPT type for editing
            url = `/clientadmin/edit_client/${clientAdminId}`;
        }

        let value = await apiCall(formData, 'POST', url, true);

        setTimeout(() => {
            loading(false);

            if (value.responseType) {
                if (value.data.success) {
                    showTypeMessage(value.data.message, "success");
                    setTimeout(() => {
                        window.location.href = "/clientadmin/";
                    }, 2000);
                } else {
                    showTypeMessage(value.data.message, "error");
                }
            } else {
                // Handle other cases if needed
            }
        }, 2000);
    }
    $("#create-clientadmin").click(async () => {
        // // Get the form element
        let form = document.getElementById("client-admin-form");

        // Check form validity
        if (form.checkValidity()) {
            // If the form is valid, call the createOrEditGptType function
            await createOrEditClientAdmin("add");
        } else {
            // If the form is not valid, show validation messages
            form.reportValidity();
        }
    });
    $("#edit-clientadmin").click(async () => {
        // // Get the form element
        let form = document.getElementById("client-admin-form");

        // Check form validity
        if (form.checkValidity()) {
            // If the form is valid, call the createOrEditGptType function
            await createOrEditClientAdmin("edit");
        } else {
            // If the form is not valid, show validation messages
            form.reportValidity();
        }
    });
    $("#edit-client").click(async () => {
        // Get the form element
        let form = document.getElementById("client-admin-form");

        // Check form validity
        if (form.checkValidity()) {
            // If the form is valid, call the createOrEditGptType function
            await createOrEditClientAdmin("edit");
        } else {
            // If the form is not valid, show validation messages
            form.reportValidity();
        }
    });

    $(".delete-clientadmin").click(async function (event) {
        event.preventDefault(); // Prevent the default behavior of the link

        // Get the GPT ID from the data attribute
        var client_id = $(this).data("client-id");

        $("#confirmClientDeleteButton").data("client_id", client_id);
        // Show the modal
        $("#deleteClientModal").modal("show");

        $("#confirmClientDeleteButton").on("click", async function () {
            var client_id = $(this).data("client_id");
            $("#deleteClientModal").modal("hide");

            try {
                // Hide the modal after confirming
                // Perform the DELETE request using the apiCall function
                let value = await apiCall({}, 'POST', '/clientadmin/delete_client/' + client_id);

                // Handle the response after the DELETE request
                loading(false);
                setTimeout(() => {
                    loading(false);

                    if (value.responseType) {
                        if (value.data.success) {
                            window.scrollTo(0, 0);
                            showTypeMessage(value.data.message, "success");
                            setTimeout(() => {
                                window.location.reload();
                            }, 2000);
                        } else {
                            window.scrollTo(0, 0);
                            showTypeMessage(value.data.message, "error");
                            setTimeout(() => {
                                window.location.reload();
                            }, 2000);
                        }
                    } else {
                        // Handle other cases if needed
                    }
                }, 2000);
            } catch (error) {
                console.error("Error:", error);
                showTypeMessage("An error occurred", "error");
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            }
        });
    });
    $('#user-search-input').on('keyup', function (event) {
        var searchQuery = $(this).val();  // Get the current value of the input field
    
        // Send AJAX request to the server to filter users
        $.ajax({
            url: "/user_management/?search=" + searchQuery, // Adjust your endpoint as necessary
            method: 'GET',
    
            success: function (response) {
                // Update the table with the filtered users
                $('tbody').html($(response).find('tbody').html());
    
                // Bind toggle click event to newly added nested user rows
                $('.toggle-nested-users').off('click').on('click', function () {
                    var userId = $(this).data('user-id');
                    var nestedRow = $('#nested-users-' + userId);
    
                    // Toggle the display of the nested user rows
                    if (nestedRow.is(':visible')) {
                        nestedRow.hide();
                        $(this).find('i').removeClass('fa-minus').addClass('fa-plus');
                    } else {
                        nestedRow.show();
                        $(this).find('i').removeClass('fa-plus').addClass('fa-minus');
                    }
                });
    
                // Automatically click the toggle button if there’s a search match
                $('.toggle-nested-users').each(function () {
                    var nestedRow = $('#nested-users-' + $(this).data('user-id'));
                    
                    // Assuming a match if the row exists; adjust criteria as needed
                    if (nestedRow.length && searchQuery) {
                        $(this).click(); // Toggle open the matching nested row
                    }
                });
    
                // Pagination setup (no changes here)
                var totalRecords = $(response).find('#pagination-info').data('total');
                var currentPage = $(response).find('#pagination-info').data('page');
                var perPage = $(response).find('#pagination-info').data('per-page');
                var totalPages = Math.ceil(totalRecords / perPage);
    
                var paginationHtml = '';
                // Add "Previous" link
                if (currentPage > 1) {
                    paginationHtml += '<li class="page-item">';
                    paginationHtml += '<a class="page-link" href="?page=' + (currentPage - 1) + '&per_page=' + perPage + '&search=' + searchQuery + '" aria-label="Previous">&laquo;</a>';
                    paginationHtml += '</li>';
                }
                for (var page = 1; page <= totalPages; page++) {
                    var activeClass = (page == currentPage) ? 'active' : '';
                    paginationHtml += '<li class="page-item ' + activeClass + '">';
                    paginationHtml += '<a class="page-link" href="?page=' + page + '&per_page=' + perPage + '&search=' + searchQuery + '">' + page + '</a>';
                    paginationHtml += '</li>';
                }
                // Add "Next" link
                if (currentPage < totalPages) {
                    paginationHtml += '<li class="page-item">';
                    paginationHtml += '<a class="page-link" href="?page=' + (currentPage + 1) + '&per_page=' + perPage + '&search=' + searchQuery + '" aria-label="Next">&raquo;</a>';
                    paginationHtml += '</li>';
                }
                $('.pagination').html(paginationHtml);
                $('.pagination .page-link').each(function () {
                    var currentUrl = $(this).attr('href');
                    var [baseUrl, queryString] = currentUrl.split('?');
                    var params = new URLSearchParams(queryString);
    
                    params.delete('search');
                    params.set('search', searchQuery);
    
                    var newUrl = baseUrl + '?' + params.toString();
                    $(this).attr('href', newUrl);
                });
            },
    
            error: function (xhr, status, error) {
                alert("Error");
                console.log("Error:", error);
            }
        });
    });
    $('#search-input').on('keyup', function (event) {
        var searchQuery = $(this).val();  // Get the current value of the input field
    
        // Send AJAX request to the server to filter users
        $.ajax({
            url: "/assistants/?search=" + searchQuery, // Adjust your endpoint as necessary
            method: 'GET',
    
            success: function (response) {
                // Update the table with the filtered users
                $('tbody').html($(response).find('tbody').html());
                // Update pagination links
                // Pagination setup (no changes here)
                var totalRecords = $(response).find('#pagination-info').data('total');
                var currentPage = $(response).find('#pagination-info').data('page');
                var perPage = $(response).find('#pagination-info').data('per-page');
                var totalPages = Math.ceil(totalRecords / perPage);
    
                var paginationHtml = '';
                // Add "Previous" link
                if (currentPage > 1) {
                    paginationHtml += '<li class="page-item">';
                    paginationHtml += '<a class="page-link" href="?page=' + (currentPage - 1) + '&per_page=' + perPage + '&search=' + searchQuery + '" aria-label="Previous">&laquo;</a>';
                    paginationHtml += '</li>';
                }
                for (var page = 1; page <= totalPages; page++) {
                    var activeClass = (page == currentPage) ? 'active' : '';
                    paginationHtml += '<li class="page-item ' + activeClass + '">';
                    paginationHtml += '<a class="page-link" href="?page=' + page + '&per_page=' + perPage + '&search=' + searchQuery + '">' + page + '</a>';
                    paginationHtml += '</li>';
                }
                // Add "Next" link
                if (currentPage < totalPages) {
                    paginationHtml += '<li class="page-item">';
                    paginationHtml += '<a class="page-link" href="?page=' + (currentPage + 1) + '&per_page=' + perPage + '&search=' + searchQuery + '" aria-label="Next">&raquo;</a>';
                    paginationHtml += '</li>';
                }
                $('.pagination').html(paginationHtml);
                $('.pagination .page-link').each(function () {
                    var currentUrl = $(this).attr('href');
                    var [baseUrl, queryString] = currentUrl.split('?');
                    var params = new URLSearchParams(queryString);
    
                    params.delete('search');
                    params.set('search', searchQuery);
    
                    var newUrl = baseUrl + '?' + params.toString();
                    $(this).attr('href', newUrl);
                });
            },
            error: function (xhr, status, error) {
                console.log("Error:", error);
                alert("An error occurred while fetching results.");
            }
        });
    });
    
});


document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.toggle-nested-users').forEach(function (button) {
        button.addEventListener('click', function () {
            var userId = this.getAttribute('data-user-id');
            var nestedRow = document.getElementById('nested-users-' + userId);

            if (nestedRow.style.display === 'none') {
                nestedRow.style.display = 'table-row'; // Show the nested users
                this.innerHTML = '<i class="fa fa-minus"></i>'; // Change + to -
            } else {
                nestedRow.style.display = 'none'; // Hide the nested users
                this.innerHTML = '<i class="fa fa-plus"></i>'; // Change - back to +
            }
        });
    });
});

$(document).ready(function () {
    $(".delete-workflow").on("click", function () {
        var workflowId = $(this).data("id"); // Retrieve the workflow ID
        if (!workflowId) {
            alert("Error: Missing workflow ID.");
            return;
        }
        $("#deleteConfirmationModal").modal("show");

        // Set up the confirm button with the appropriate action
        $("#deleteConfirmButton").off("click").on("click", async function () {
        // Perform AJAX request
        $.ajax({
            url: `/workflows/delete_workflow/${workflowId}`, // URL to the backend
            type: "POST", // HTTP POST request
            headers: {
                'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
              },
            success: function (response) { 
                if (response.success) {
                    // Optionally, you can remove the deleted workflow from the DOM
                    $(`#workflow-${workflowId}`).remove();
                    showTypeMessage(response.message, "success");
                    setTimeout(() => {
                        window.location.href = "/workflows/";
                    }, 2000);
                } else {
                    showTypeMessage(response.message, "error");
                    setTimeout(() => {
                        window.location.href = "/workflows/";
                    }, 2000);
                }
                $("#deleteConfirmationModal").modal("hide");
            },
            error: function (xhr) { alert("error")
                const response = xhr.responseJSON;
                showTypeMessage(response.message, "error");
                $("#deleteConfirmationModal").modal("hide");
            },
        });
    });
    });
});

