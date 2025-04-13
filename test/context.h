#pragma once

#include <ranges>
#include <concepts>
#include <algorithm>

namespace vulkan_context
{
	template<class T>
	struct construct_cpo
	{
		decltype(auto) operator()(auto&&... params) const noexcept
		{
			return T{ ::std::forward<decltype(params)>(params)... };
		}
	};
	template<class T>
	inline constexpr construct_cpo<T> constructor{};
	
	decltype(auto) contains_range(::std::ranges::input_range auto const& range, ::std::ranges::input_range auto const& sub_range) noexcept
		requires ::std::equality_comparable_with<::std::ranges::range_value_t<decltype(range)>, ::std::ranges::range_value_t<decltype(sub_range)>>
	{
		return ::std::ranges::all_of(sub_range, [&](auto const& e) noexcept
			{
				return ::std::ranges::find(range, e) != ::std::ranges::end(range);
			});
	}

	struct instance_loader
	{
		using self_type = instance_loader;

		::vk2::handle::instance const _instance;

		auto load(char const* name) const noexcept
		{
			return ::vk2::func::get_instance_proc_addr(_instance, name);
		}
		auto load(::nagisa::strings::character_range auto const& name) const noexcept
			requires requires { {::nagisa::strings::c_str(name) } -> ::std::convertible_to<char const*>; }
		{
			return self_type::load(::nagisa::strings::c_str(name));
		}
	};
}