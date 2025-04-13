#include <vulkan/vulkan.h>
#include <nagisa/external/glfw/glfw.h>
#include <nagisa/external/glfw/api/vulkan.h>

#include <vulkan_killer/core/1_0/type.h>
#include <vulkan_killer/core/1_0/function.h>
#include <vulkan_killer/ext/debug_utils/type.h>
#include <vulkan_killer/ext/debug_utils/function.h>
#include <vulkan_killer/khr/surface/type.h>
#include <vulkan_killer/khr/surface/function.h>
#include <vulkan_killer/khr/swapchain/type.h>
#include <vulkan_killer/khr/swapchain/function.h>

#include <set>
#include <vector>
#include <iostream>
#include <optional>
#include <algorithm>
#include <fstream>

namespace vk2 = ::vulkan_killer;
namespace nfw = ::nagisa::external::glfw;

#include <nagisa/concept/concept.h>
#include <nagisa/string/string.h>
#include <nagisa/symbol_loader/symbol_loader.h>

#include "./context.h"

inline constexpr auto enable_validation_layers =
#ifdef NDEBUG
false
#else
true
#endif
;


#include <fast_io.h>

struct queue_family_indices
{
	::std::optional<::std::uint32_t> graphics_family;
	::std::optional<::std::uint32_t> present_family;

	constexpr auto is_complete() const noexcept
	{
		return graphics_family.has_value() && present_family.has_value();
	}
};



struct hello_triangle_application
{
	constexpr static auto validation_layers = ::std::array{ "VK_LAYER_KHRONOS_validation", };
	constexpr static auto device_extensions = ::std::array{ VK_KHR_SWAPCHAIN_EXTENSION_NAME, };


	::nfw::vulkan_instance _fw_instance{};
	::nfw::window _window;

	::vk2::handle::instance _instance{};
	::vulkan_context::instance_loader _instance_loader;
	struct symbol_table
	{
		::vk2::ext::func::create_debug_utils_messenger_cpo::symbol_type* const create_debug_utils_messenger;
		::vk2::ext::func::destroy_debug_utils_messenger_cpo::symbol_type* const destroy_debug_utils_messenger;
	} _symbol_table;

	::vk2::ext::handle::debug_utils_messenger _debug_messenger{};
	::vk2::khr::handle::surface _surface = VK_NULL_HANDLE;
	struct
	{
		::vk2::khr::handle::swapchain handle = VK_NULL_HANDLE;
		::std::vector<::vk2::handle::image> images{};
		::std::vector<::vk2::handle::image_view> image_views{};
		::vk2::format image_format{};
		::vk2::extent2d extent{};
		::std::vector<::vk2::handle::framebuffer> framebuffers{};
	}_swapchain{};

	::vk2::handle::physical_device _physical_device = VK_NULL_HANDLE;
	::vk2::handle::device _device{};

	::vk2::handle::queue _graphics_queue{};
	::vk2::handle::queue _present_queue{};

	::vk2::handle::render_pass _render_pass = VK_NULL_HANDLE;
	::vk2::handle::pipeline_layout _pipeline_layout = VK_NULL_HANDLE;
	::vk2::handle::pipeline _graphics_pipeline = VK_NULL_HANDLE;
	::vk2::handle::command_pool _command_pool = VK_NULL_HANDLE;
	::vk2::handle::command_buffer _command_buffer = VK_NULL_HANDLE;

	::vk2::handle::semaphore _image_available_semaphore = VK_NULL_HANDLE;
	::vk2::handle::semaphore _render_finished_semaphore = VK_NULL_HANDLE;
	::vk2::handle::fence _in_flight_fence = VK_NULL_HANDLE;

	static decltype(auto) _check_validation_layer_support(::std::ranges::input_range auto const& validation_layers) noexcept
		requires ::std::same_as<::std::remove_cv_t<::std::ranges::range_value_t<decltype(validation_layers)>>, ::std::string_view>
	{
		uint32_t [[indeterminate]] layer_count;
		::vk2::func::enumerate_instance_layer_properties(&layer_count, nullptr);
		::std::vector<::vk2::layer_properties> available_layers(layer_count);
		::vk2::func::enumerate_instance_layer_properties(&layer_count, available_layers.data());

		auto layer_names = available_layers
			| ::std::views::transform([](::vk2::layer_properties const& properties) noexcept { return ::std::string_view(properties.layer_name); });

		return vulkan_context::contains_range(layer_names, validation_layers);
	}

	static auto _create_instance(::nfw::vulkan_instance const& instance)
	{
		if constexpr (enable_validation_layers)
		{
			if (!_check_validation_layer_support(validation_layers | ::std::views::transform(::vulkan_context::constructor<::std::string_view>)))
			{
				throw ::std::runtime_error("validation layers requested, but not available!");
			}
		}

		::vk2::application_info app_info{
			.application_name = "Hello Triangle",
			.application_version = VK_MAKE_VERSION(1, 0, 0),
			.engine_name = "No Engine",
			.engine_version = VK_MAKE_VERSION(1, 0, 0),
			.api_version = VK_API_VERSION_1_0,
		};

		::vk2::instance_create_info create_info{
			.structure_next = nullptr,
			.application_info_ = &app_info,
			.enabled_layer_count = 0,
		};


		if constexpr (enable_validation_layers)
		{
			auto extensions = ::std::ranges::to<::std::vector<char const*>>(instance.get_required_instance_extensions());
			extensions.push_back(VK_EXT_DEBUG_UTILS_EXTENSION_NAME);
			create_info.enabled_extension_count = static_cast<::std::uint32_t>(::std::ranges::size(extensions));
			create_info.enabled_extension_names_ptr = ::std::ranges::data(extensions);

			::vk2::ext::debug_utils_messenger_create_info debug_create_info{};
			populate_debug_messenger_create_info(debug_create_info);

			create_info.enabled_layer_count = static_cast<::std::uint32_t>(::std::ranges::size(validation_layers));
			create_info.enabled_layer_names_ptr = ::std::ranges::data(validation_layers);
			create_info.structure_next = &debug_create_info;

			::vk2::handle::instance result;
			if (::vk2::func::create_instance(&create_info, nullptr, &result) != ::vk2::result::success)
			{
				throw ::std::runtime_error("failed to create instance!");
			}
			return result;
		}
		else
		{
			auto extensions = instance.get_required_instance_extensions();
			create_info.enabled_extension_count = static_cast<::std::uint32_t>(::std::ranges::size(extensions));
			create_info.enabled_extension_names_ptr = ::std::ranges::data(extensions);

			::vk2::handle::instance result;
			if (::vk2::func::create_instance(&create_info, nullptr, &result) != ::vk2::result::success)
			{
				throw ::std::runtime_error("failed to create instance!");
			}
			return result;
		}
	}

	hello_triangle_application()
		: _window(_fw_instance.create_window(800u, 600u, "vulkan"))
		, _instance(_create_instance(_fw_instance))
		, _instance_loader{ _instance }
		, _symbol_table{
			.create_debug_utils_messenger = ::nagisa::symbol_loader::typed_load<::vk2::ext::func::create_debug_utils_messenger_cpo>(_instance_loader),
			.destroy_debug_utils_messenger = ::nagisa::symbol_loader::typed_load<::vk2::ext::func::destroy_debug_utils_messenger_cpo>(_instance_loader),
		}
	{
		::nfw::set_window_hint<::nfw::hint::resizable>(_fw_instance, false);
		if constexpr(::enable_validation_layers)
		{
			::vk2::ext::debug_utils_messenger_create_info create_info;
			populate_debug_messenger_create_info(create_info);

			if (_symbol_table.create_debug_utils_messenger(_instance, &create_info, nullptr, &_debug_messenger) != ::vk2::result::success)
				throw ::std::runtime_error("failed to set up debug messenger!");
		}
		if (::vk2::to_killer(_fw_instance.create_window_surface(::vk2::to_vulkan_c(_instance), _window.handle(), nullptr, ::vk2::to_vulkan_c(&_surface))) != ::vk2::result::success)
		{
			throw ::std::runtime_error("failed to create window surface!");
		}

		_pick_physical_device();
		_create_logical_device();
		// create swap chain
		{
			::vk2::khr::swapchain_create_info create_info{};
			create_info.surface_ = _surface;
			create_info.image_array_layers = 1;
			create_info.image_usage = ::vk2::image_usage_bits::color_attachment;
			{
				::vk2::khr::surface_capabilities [[indeterminate]] capabilities;
				::vk2::khr::func::get_physical_device_surface_capabilities(_physical_device, _surface, &capabilities);
				create_info.min_image_count = capabilities.min_image_count + 1;

				auto [width, height] = _window.framebuffer_size();
				create_info.image_extent = _swapchain.extent = ::vk2::extent2d{
					.width = ::std::clamp<::std::uint32_t>(width, capabilities.min_image_extent.width, capabilities.max_image_extent.width),
					.height = ::std::clamp<::std::uint32_t>(height, capabilities.min_image_extent.height, capabilities.max_image_extent.height),
				};
				create_info.pre_transform = capabilities.current_transform;
			}
			{
				::std::uint32_t [[indeterminate]] format_count;
				::vk2::khr::func::get_physical_device_surface_formats(_physical_device, _surface, &format_count, nullptr);
				::std::vector<::vk2::khr::surface_format> formats(format_count);
				::vk2::khr::func::get_physical_device_surface_formats(_physical_device, _surface, &format_count, formats.data());
				create_info.image_format = _swapchain.image_format = formats.front().format_;
				create_info.image_color_space = formats.front().color_space_;
			}
			{
				::std::uint32_t [[indeterminate]] present_mode_count;
				::vk2::khr::func::get_physical_device_surface_present_modes(_physical_device, _surface, &present_mode_count, nullptr);
				::std::vector<::vk2::khr::present_mode> present_modes(present_mode_count);
				::vk2::khr::func::get_physical_device_surface_present_modes(_physical_device, _surface, &present_mode_count, present_modes.data());
				create_info.present_mode_ = present_modes.front();
			}
			auto indices = find_queue_families(_physical_device);
			auto queue_family_indices = ::std::array{ indices.graphics_family.value(), indices.present_family.value() };
			if (indices.graphics_family != indices.present_family)
			{
				create_info.image_sharing_mode = ::vk2::sharing_mode::concurrent;
				create_info.queue_family_index_count = 2;
				create_info.queue_family_indices = queue_family_indices.data();
			}
			else
			{
				create_info.image_sharing_mode = ::vk2::sharing_mode::exclusive;
			}
			create_info.composite_alpha = ::vk2::khr::composite_alpha_bits::opaque;
			create_info.clipped = true;
			create_info.old_swapchain = VK_NULL_HANDLE;

			if (::vk2::khr::func::create_swapchain(_device, &create_info, nullptr, &_swapchain.handle) != ::vk2::result::success) 
				throw ::std::runtime_error("failed to create swap chain!");
			{
				::std::uint32_t [[indeterminate]] image_count;
				::vk2::khr::func::get_swapchain_images(_device, _swapchain.handle, &image_count, nullptr);
				_swapchain.images.resize(image_count);
				::vk2::khr::func::get_swapchain_images(_device, _swapchain.handle, &image_count, _swapchain.images.data());
			}
		}
		// create image views
		{
			_swapchain.image_views.resize(::std::ranges::size(_swapchain.images), VK_NULL_HANDLE);
			for (auto&& [image, image_view] : ::std::views::zip(_swapchain.images, _swapchain.image_views))
			{
				::vk2::image_view_create_info create_info{};
				create_info.image_ = image;
				create_info.view_type = ::vk2::image_view_type::_2_d;
				create_info.format_ = _swapchain.image_format;
				create_info.components = ::vk2::component_mapping{
					.r = ::vk2::component_swizzle::identity,
					.g = ::vk2::component_swizzle::identity,
					.b = ::vk2::component_swizzle::identity,
					.a = ::vk2::component_swizzle::identity,
				};
				create_info.subresource_range.aspect_mask = ::vk2::image_aspect_bits::color;
				create_info.subresource_range.base_mip_level = 0;
				create_info.subresource_range.level_count = 1;
				create_info.subresource_range.base_array_layer = 0;
				create_info.subresource_range.layer_count = 1;
				if (::vk2::func::create_image_view(_device, &create_info, nullptr, &image_view) != ::vk2::result::success)
					throw ::std::runtime_error("failed to create image views!");
			}
		}
		// create render pass
		{
			auto color_attachment = ::vk2::attachment_description{
				.format_ = _swapchain.image_format,
				.samples = ::vk2::sample_count_bits::_1,
				.load_op = ::vk2::attachment_load_op::clear,
				.store_op = ::vk2::attachment_store_op::store,
				.stencil_load_op = ::vk2::attachment_load_op::dont_care,
				.stencil_store_op = ::vk2::attachment_store_op::dont_care,
				.initial_layout = ::vk2::image_layout::undefined,
				.final_layout = ::vk2::khr::image_layout::present_src,
			};
			auto color_attachment_ref = ::vk2::attachment_reference{
				.attachment = 0,
				.layout = ::vk2::image_layout::color_attachment_optimal,
			};
			auto subpass = ::vk2::subpass_description{
				.pipeline_bind_point_ = ::vk2::pipeline_bind_point::graphics,
				.color_attachment_count = 1,
				.color_attachments = &color_attachment_ref,
			};
			auto dependency = ::vk2::subpass_dependency{
				.src_subpass = VK_SUBPASS_EXTERNAL,
				.dst_subpass = 0,
				.src_stage_mask = ::vk2::pipeline_stage_bits::color_attachment_output,
				.dst_stage_mask = ::vk2::pipeline_stage_bits::color_attachment_output,
				.src_access_mask = 0,
				.dst_access_mask = ::vk2::access_bits::color_attachment_write,
			};
			auto render_pass_info = ::vk2::render_pass_create_info{
				.attachment_count = 1,
				.attachments = &color_attachment,
				.subpass_count = 1,
				.subpasses = &subpass,
				.dependency_count = 1,
				.dependencies = &dependency,
			};

			if (::vk2::func::create_render_pass(_device, &render_pass_info, nullptr, &_render_pass) != ::vk2::result::success)
				throw ::std::runtime_error("failed to create render pass!");
		}
		// create graphics pipeline
		{
			constexpr auto create_shader_module = [](::vk2::handle::device device, ::std::ranges::contiguous_range auto const& code)
				requires requires{ reinterpret_cast<::std::uint32_t const*>(::std::ranges::data(code)); }
				{
					::vk2::shader_module_create_info create_info{};
					create_info.code_size = ::std::ranges::size(code) * sizeof(::std::ranges::range_value_t<decltype(code)>);
					create_info.code = reinterpret_cast<::std::uint32_t const*>(::std::ranges::data(code));
					::vk2::handle::shader_module result;
					if (::vk2::func::create_shader_module(device, &create_info, nullptr, &result) != ::vk2::result::success)
						throw ::std::runtime_error("failed to create shader module!");
					return result;
				};
			auto vert_shader_module = create_shader_module(_device, ::fast_io::native_file_loader("shaders/vert.spv"));
			auto frag_shader_module = create_shader_module(_device, ::fast_io::native_file_loader("shaders/frag.spv"));

			auto vert_shader_stage_info = ::vk2::pipeline_shader_stage_create_info{
				.stage = ::vk2::shader_stage_bits::vertex,
				.module = vert_shader_module,
				.name = "main",
			};
			auto frag_shader_stage_info = ::vk2::pipeline_shader_stage_create_info{
				.stage = ::vk2::shader_stage_bits::fragment,
				.module = frag_shader_module,
				.name = "main",
			};
			auto shader_stages = ::std::array{ vert_shader_stage_info, frag_shader_stage_info };
			auto vertex_input_info = ::vk2::pipeline_vertex_input_state_create_info{
				.vertex_binding_description_count = 0,
				.vertex_attribute_description_count = 0,
			};
			auto input_assembly = ::vk2::pipeline_input_assembly_state_create_info{
				.topology = ::vk2::primitive_topology::triangle_list,
				.primitive_restart_enable = VK_FALSE,
			};
			auto viewport_state = ::vk2::pipeline_viewport_state_create_info{
				.viewport_count = 1,
				.scissor_count = 1,
			};
			auto rasterizer = ::vk2::pipeline_rasterization_state_create_info{
				.depth_clamp_enable = VK_FALSE,
				.rasterizer_discard_enable = VK_FALSE,
				.polygon_mode_ = ::vk2::polygon_mode::fill,
				.cull_mode = ::vk2::cull_mode_bits::back,
				.front_face_ = ::vk2::front_face::clockwise,
				.depth_bias_enable = VK_FALSE,
				.line_width = 1.0f,
			};
			auto multisampling = ::vk2::pipeline_multisample_state_create_info{
				.rasterization_samples = ::vk2::sample_count_bits::_1,
				.sample_shading_enable = VK_FALSE,
			};
			auto color_blend_attachment = ::vk2::pipeline_color_blend_attachment_state{
				.blend_enable = VK_FALSE,
				.color_write_mask = ::vk2::color_component_bits::r | ::vk2::color_component_bits::g | ::vk2::color_component_bits::b | ::vk2::color_component_bits::a,
			};
			auto color_blending = ::vk2::pipeline_color_blend_state_create_info{
				.logic_op_enable = VK_FALSE,
				.logic_op_ = ::vk2::logic_op::copy,
				.attachment_count = 1,
				.attachments = &color_blend_attachment,
				.blend_constants = { 0.0f, 0.0f, 0.0f, 0.0f },
			};
			auto dynamic_states = ::std::array{ ::vk2::dynamic_state::viewport, ::vk2::dynamic_state::scissor };
			auto dynamic_state = ::vk2::pipeline_dynamic_state_create_info{
				.dynamic_state_count = static_cast<::std::uint32_t>(::std::ranges::size(dynamic_states)),
				.dynamic_states = ::std::ranges::data(dynamic_states),
			};
			auto pipeline_layout_info = ::vk2::pipeline_layout_create_info{
				.set_layout_count = 0,
				.push_constant_range_count = 0,
			};
			if (::vk2::func::create_pipeline_layout(_device, &pipeline_layout_info, nullptr, &_pipeline_layout) != ::vk2::result::success)
				throw ::std::runtime_error("failed to create pipeline layout!");

			auto pipeline_info = ::vk2::graphics_pipeline_create_info{
				.stage_count = static_cast<::std::uint32_t>(::std::ranges::size(shader_stages)),
				.stages = ::std::ranges::data(shader_stages),
				.vertex_input_state = &vertex_input_info,
				.input_assembly_state = &input_assembly,
				.viewport_state = &viewport_state,
				.rasterization_state = &rasterizer,
				.multisample_state = &multisampling,
				.color_blend_state = &color_blending,
				.dynamic_state = &dynamic_state,
				.layout = _pipeline_layout,
				.render_pass_ = _render_pass,
				.subpass = 0,
				.base_pipeline_handle = VK_NULL_HANDLE,
			};
			if (::vk2::func::create_graphics_pipelines(_device, VK_NULL_HANDLE, 1, &pipeline_info, nullptr, &_graphics_pipeline) != ::vk2::result::success)
				throw ::std::runtime_error("failed to create graphics pipeline!");

			::vk2::func::destroy_shader_module(_device, vert_shader_module, nullptr);
			::vk2::func::destroy_shader_module(_device, frag_shader_module, nullptr);
		}
		// create framebuffer
		{
			_swapchain.framebuffers.resize(_swapchain.image_views.size());

			for (auto view : _swapchain.image_views)
			{
				auto attachments = ::std::array{ view };
				auto framebuffer_info = ::vk2::framebuffer_create_info{
					.render_pass_ = _render_pass,
					.attachment_count = static_cast<::std::uint32_t>(::std::ranges::size(attachments)),
					.attachments = ::std::ranges::data(attachments),
					.width = _swapchain.extent.width,
					.height = _swapchain.extent.height,
					.layers = 1,
				};

				if (::vk2::func::create_framebuffer(_device, &framebuffer_info, nullptr, &_swapchain.framebuffers[::std::ranges::distance(_swapchain.image_views.begin(), ::std::ranges::find(_swapchain.image_views, view))]) != ::vk2::result::success)
					throw ::std::runtime_error("failed to create framebuffer!");
			}
		}
		// create command pool
		{
			auto queue_family_indices = find_queue_families(_physical_device);
			auto pool_info = ::vk2::command_pool_create_info{
				.flags = ::vk2::command_pool_create_bits::reset_command_buffer,
				.queue_family_index = queue_family_indices.graphics_family.value(),
			};
			if (::vk2::func::create_command_pool(_device, &pool_info, nullptr, &_command_pool) != ::vk2::result::success)
				throw ::std::runtime_error("failed to create command pool!");
		}
		// create command buffer
		{
			auto allocate_info = ::vk2::command_buffer_allocate_info{
				.command_pool_ = _command_pool,
				.level = ::vk2::command_buffer_level::primary,
				.command_buffer_count = 1,
			};
			if (::vk2::func::allocate_command_buffers(_device, &allocate_info, &_command_buffer) != ::vk2::result::success)
				throw ::std::runtime_error("failed to allocate command buffers!");
		}
		// create sync objects
		{
			auto semaphore_info = ::vk2::semaphore_create_info{};

			auto fence_info = ::vk2::fence_create_info{
				.flags = ::vk2::fence_create_bits::signaled,
			};

			if (::vk2::func::create_semaphore(_device, &semaphore_info, nullptr, &_image_available_semaphore) != ::vk2::result::success)
				throw ::std::runtime_error("failed to create semaphore!");
			if (::vk2::func::create_semaphore(_device, &semaphore_info, nullptr, &_render_finished_semaphore) != ::vk2::result::success)
				throw ::std::runtime_error("failed to create semaphore!");
			if (::vk2::func::create_fence(_device, &fence_info, nullptr, &_in_flight_fence) != ::vk2::result::success)
				throw ::std::runtime_error("failed to create fence!");
		}
	}
	~hello_triangle_application() noexcept
	{
		::vk2::func::destroy_semaphore(_device, _render_finished_semaphore, nullptr);
		::vk2::func::destroy_semaphore(_device, _image_available_semaphore, nullptr);
		::vk2::func::destroy_fence(_device, _in_flight_fence, nullptr);

		::vk2::func::destroy_command_pool(_device, _command_pool, nullptr);

		for (auto framebuffer : _swapchain.framebuffers)
		{
			::vk2::func::destroy_framebuffer(_device, framebuffer, nullptr);
		}

		::vk2::func::destroy_pipeline(_device, _graphics_pipeline, nullptr);
		::vk2::func::destroy_pipeline_layout(_device, _pipeline_layout, nullptr);
		::vk2::func::destroy_render_pass(_device, _render_pass, nullptr);

		for (auto image_view : _swapchain.image_views)
		{
			::vk2::func::destroy_image_view(_device, image_view, nullptr);
		}
		::vk2::khr::func::destroy_swapchain(_device, _swapchain.handle, nullptr);
		::vk2::func::destroy_device(_device, nullptr);

		if constexpr (enable_validation_layers)
		{
			_symbol_table.destroy_debug_utils_messenger(_instance, _debug_messenger, nullptr);
		}
		::vk2::khr::func::destroy_surface(_instance, _surface, nullptr);
		::vk2::func::destroy_instance(_instance, nullptr);
	}

	void _record_command_buffer(::vk2::handle::command_buffer command_buffer, ::std::uint32_t image_index)
	{
		auto begin_info = ::vk2::command_buffer_begin_info{};
		if (::vk2::func::begin_command_buffer(command_buffer, &begin_info) != ::vk2::result::success)
			throw ::std::runtime_error("failed to begin recording command buffer!");

		{
			auto clear_color = ::vk2::clear_value{
				.color = ::vk2::clear_color_value{
					.float32 = { 0.0f, 0.0f, 0.0f, 1.0f }
				}
			};
			auto render_pass_info = ::vk2::render_pass_begin_info{
				.render_pass_ = _render_pass,
				.framebuffer_ = _swapchain.framebuffers[image_index],
				.render_area = ::vk2::rect2d{
					.offset = { 0, 0 },
					.extent = _swapchain.extent,
				},
				.clear_value_count = 1,
				.clear_values = &clear_color,
			};

			::vk2::func::cmd_begin_render_pass(_command_buffer, &render_pass_info, ::vk2::subpass_contents::inline_);
			::vk2::func::cmd_bind_pipeline(_command_buffer, ::vk2::pipeline_bind_point::graphics, _graphics_pipeline);
			auto viewport = ::vk2::viewport{
				.x = 0.0f,
				.y = 0.0f,
				.width = static_cast<float>(_swapchain.extent.width),
				.height = static_cast<float>(_swapchain.extent.height),
				.min_depth = 0.0f,
				.max_depth = 1.0f,
			};
			::vk2::func::cmd_set_viewport(_command_buffer, 0, 1, &viewport);
			auto scissor = ::vk2::rect2d{
				.offset = { 0, 0 },
				.extent = _swapchain.extent,
			};
			::vk2::func::cmd_set_scissor(_command_buffer, 0, 1, &scissor);

			::vk2::func::cmd_draw(_command_buffer, 3, 1, 0, 0);
			::vk2::func::cmd_end_render_pass(_command_buffer);
		}
		if (::vk2::func::end_command_buffer(_command_buffer) != ::vk2::result::success)
			throw ::std::runtime_error("failed to record command buffer!");
	}

	void run()
	{
		while (!_window.should_close())
		{
			_fw_instance.poll_events();
			// draw frame
			{
				::vk2::func::wait_for_fences(_device, 1, &_in_flight_fence, VK_TRUE, ::std::numeric_limits<::std::uint64_t>::max());
				::vk2::func::reset_fences(_device, 1, &_in_flight_fence);

				::std::uint32_t [[indeterminate]] image_index;
				::vk2::khr::func::acquire_next_image(_device, _swapchain.handle, ::std::numeric_limits<::std::uint64_t>::max(), _image_available_semaphore, VK_NULL_HANDLE, &image_index);

				::vk2::func::reset_command_buffer(_command_buffer, 0);
				_record_command_buffer(_command_buffer, image_index);

				auto wait_semaphore = ::std::array{ _image_available_semaphore };
				auto wait_stages = ::std::array{ static_cast<::vk2::pipeline_stage_flag>(::vk2::pipeline_stage_bits::color_attachment_output) };
				auto signal_semaphore = ::std::array{ _render_finished_semaphore };

				auto submit_info = ::vk2::submit_info{
					.wait_semaphore_count = 1,
					.wait_semaphores = ::std::ranges::data(wait_semaphore),
					.wait_dst_stage_mask = ::std::ranges::data(wait_stages),
					.command_buffer_count = 1,
					.command_buffers = &_command_buffer,
					.signal_semaphore_count = 1,
					.signal_semaphores = ::std::ranges::data(signal_semaphore),
				};
				if (::vk2::func::queue_submit(_graphics_queue, 1, &submit_info, _in_flight_fence) != ::vk2::result::success)
					throw ::std::runtime_error("failed to submit draw command buffer!");

				auto present_info = ::vk2::khr::present_info{
					.wait_semaphore_count = 1,
					.wait_semaphores = ::std::ranges::data(signal_semaphore),
					.swapchain_count = 1,
					.swapchains = &_swapchain.handle,
					.image_indices = &image_index,
				};
				::vk2::khr::func::queue_present(_present_queue, &present_info);
			}
		}
		::vk2::func::device_wait_idle(_device);
	}

	constexpr static void populate_debug_messenger_create_info(::vk2::ext::debug_utils_messenger_create_info& create_info) noexcept
	{
		create_info = {};
		using namespace ::vk2::ext::debug_utils_message_severity_bits;
		using namespace ::vk2::ext::debug_utils_message_type_bits;
		create_info.message_severity = verbose | warning | error;
		create_info.message_type = general | validation | performance;
		create_info.user_callback = debug_callback;
	}

	auto find_queue_families(::vk2::handle::physical_device device) const {
		queue_family_indices indices{};

		::std::uint32_t [[indeterminate]] queue_family_count;
		::vk2::func::get_physical_device_queue_family_properties(device, &queue_family_count, nullptr);
		::std::vector<::vk2::queue_family_properties> queue_families(queue_family_count);
		::vk2::func::get_physical_device_queue_family_properties(device, &queue_family_count, queue_families.data());

		auto i = 0u;
		for (const auto& queue_family : queue_families) {
			if (queue_family.queue_flags & ::vk2::queue_bits::graphics)
				indices.graphics_family = i;

			::vk2::bool32 present_support = false;
			::vk2::khr::func::get_physical_device_surface_support(device, i, _surface, &present_support);
			if (present_support)
				indices.present_family = i;
			if (indices.is_complete())
				break;
			i++;
		}

		return indices;
	}

	bool is_device_suitable(::vk2::handle::physical_device device) const noexcept
	{
		if (!find_queue_families(device).is_complete())
			return false;
		// check device
		{
			::std::uint32_t [[indeterminate]] extension_count;
			::vk2::func::enumerate_device_extension_properties(device, nullptr, &extension_count, nullptr);
			::std::vector<::vk2::extension_properties> available_extensions(extension_count);
			::vk2::func::enumerate_device_extension_properties(device, nullptr, &extension_count, available_extensions.data());

			if (!::vulkan_context::contains_range(
				available_extensions | ::std::views::transform([](::vk2::extension_properties const& properties) noexcept { return ::std::string_view(properties.extension_name); }),
				device_extensions | ::std::views::transform(::vulkan_context::constructor<::std::string_view>)
			))
				return false;
		}
		// check swap chain support
		{
			::std::uint32_t [[indeterminate]] format_count;
			::vk2::khr::func::get_physical_device_surface_formats(device, _surface, &format_count, nullptr);
			if (!format_count)
				return false;
			::std::vector<::vk2::khr::surface_format> formats(format_count);
			::vk2::khr::func::get_physical_device_surface_formats(device, _surface, &format_count, formats.data());
			if (::std::ranges::empty(formats))
				return false;

			::std::uint32_t [[indeterminate]] present_mode_count;
			::vk2::khr::func::get_physical_device_surface_present_modes(device, _surface, &present_mode_count, nullptr);
			if (!present_mode_count)
				return false;
			::std::vector<::vk2::khr::present_mode> present_modes(present_mode_count);
			::vk2::khr::func::get_physical_device_surface_present_modes(device, _surface, &present_mode_count, present_modes.data());
			if (::std::ranges::empty(present_modes))
				return false;
		}
		return true;
	}

	void _pick_physical_device()
	{
		::std::uint32_t device_count = 0;
		::vk2::func::enumerate_physical_devices(_instance, &device_count, nullptr);

		if (!device_count) 
		{
			throw ::std::runtime_error("failed to find GPUs with Vulkan support!");
		}

		::std::vector<::vk2::handle::physical_device> devices(device_count);
		::vk2::func::enumerate_physical_devices(_instance, &device_count, devices.data());

		for (const auto& device : devices) {
			if (is_device_suitable(device)) {
				_physical_device = device;
				break;
			}
		}

		if (_physical_device == VK_NULL_HANDLE) {
			throw ::std::runtime_error("failed to find a suitable GPU!");
		}
	}

	void _create_logical_device() {
		auto [graphics_family, present_family] = find_queue_families(_physical_device);

		auto queue_create_infos = ::std::vector<::vk2::device_queue_create_info>{};
		auto unique_queue_families = ::std::set{
			graphics_family.value(),
			present_family.value()
		};

		auto queue_priority = 1.0f;
		for (auto queue_family : unique_queue_families) {
			::vk2::device_queue_create_info queue_create_info{};
			queue_create_info.queue_family_index = queue_family;
			queue_create_info.queue_count = 1;
			queue_create_info.queue_priorities = &queue_priority;
			queue_create_infos.push_back(queue_create_info);
		}

		::vk2::physical_device_features device_features{};

		::vk2::device_create_info create_info{};

		create_info.queue_create_info_count = static_cast<uint32_t>(queue_create_infos.size());
		create_info.queue_create_infos = queue_create_infos.data();

		create_info.enabled_features = &device_features;

		

		if (enable_validation_layers) {
			create_info.enabled_layer_count = static_cast<uint32_t>(validation_layers.size());
			create_info.enabled_layer_names_ptr = validation_layers.data();
		}
		else {
			create_info.enabled_layer_count = 0;
		}
		create_info.enabled_extension_count = static_cast<::std::uint32_t>(::std::ranges::size(device_extensions));
		create_info.enabled_extension_names_ptr = device_extensions.data();

		if (::vk2::func::create_device(_physical_device, &create_info, nullptr, &_device) != ::vk2::result::success) {
			throw std::runtime_error("failed to create logical device!");
		}

		::vk2::func::get_device_queue(_device, graphics_family.value(), 0, &_graphics_queue);
		::vk2::func::get_device_queue(_device, present_family.value(), 0, &_present_queue);
	}

	static VKAPI_ATTR ::vk2::bool32 VKAPI_CALL debug_callback(
		::vk2::ext::debug_utils_message_severity_bits::underlying_type message_severity, 
		::vk2::ext::debug_utils_message_type_flag message_type, 
		::vk2::ext::debug_utils_messenger_callback_data const* callback_data, 
		void* user_data
	) noexcept {
		std::cerr << "validation layer: " << callback_data->message << std::endl;

		return VK_FALSE;
	}
};

int main() {
	
	hello_triangle_application app{};
	try {
		app.run();
	}
	catch (const std::exception& e) {
		std::cerr << e.what() << std::endl;
		return 1;
	}

	return 0;
}
